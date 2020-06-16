###############################################################################
#  Project: UMDLoop
#  Repository: https://github.com/umdloop/state-machines
#  File: fsm_gen.py
###############################################################################
#  Purpose:
#
#     This tool generates a FSM skeleton from a *.dot graph description
#     using the tinyfsm C++ library.
###############################################################################
#  Usage: fsm_gen.py [-h] [-s] infile outdir
#
#  Generate C++ state machine from dotfile graph.
#
#  positional arguments:
#  infile       a *.dot file to be converted.
#  outdir       directory to output generated code
#
#  optional arguments:
#    -h, --help   show this help message and exit
#    -s, --stubs  forces stub generation even when this tool would otherwise
#                 perform code generation.
###############################################################################
#  Dependencies
#     * python3
#     * libgraphviz-dev
#     * networkx
###############################################################################
#  Change History:
#
#    Author      Date      Description of Change
#  ----------  --------  --------------------------------------------------
#  Ryan W.     10-26-19  Initial version
#  Minya R.    11-04-19  Minor Source Generation Bugfix
#  Ryan W.     11-11-19  Major update, added disjoint machine support
#  Ryan W.     11-30-19  Added fsm_fifo, fsm_driver, user_states
#  Minya R.    02-17-20  Fixed multigraph transition bug
###############################################################################

from pathlib import Path
from shutil import copyfile
import networkx as nx
import argparse
import os
import re

###############################################################################
#  Utils
###############################################################################

CODEGEN = True

def process_graph(infile, outdir):
    G = nx.drawing.nx_agraph.read_dot(infile)
    
    tinyfsm = os.path.join(outdir, 'Inc/tinyfsm.hpp')
    reference = os.path.join(Path(__file__).parent.absolute(), 'tinyfsm.hpp')
    copyfile(reference, tinyfsm, follow_symlinks=True)
    
    events_header = os.path.join(outdir, 'Inc/Events.hpp')
    gen_events_header(G, events_header)
    
    fifo_source = os.path.join(outdir, 'Src/fsm_fifo.cpp')
    fifo_header = os.path.join(outdir, 'Inc/fsm_fifo.hpp')
    gen_fsm_fifo(G, fifo_source, fifo_header)
    
    driver_source = os.path.join(outdir, 'Src/fsm_driver.cpp')
    driver_header = os.path.join(outdir, 'Inc/fsm_driver.hpp')
    gen_fsm_driver(G, driver_source, driver_header)
    
    states_source = os.path.join(outdir, 'Src/user_states.cpp')
    states_header = os.path.join(outdir, 'Inc/user_states.hpp')
    gen_user_states(G, states_source, states_header)
    
    entries = entry_states(G)
    for i in range (0, len(entries)):
        name = f'FSM{i+1}'
        sub = get_subgraph_from_entry(G, entries[i])
        process_machine(sub, name, entries[i], outdir)

def process_machine(G, machine, entry, outdir):
    fsm_header = os.path.join(outdir, f'Inc/{machine}.hpp')
    fsm_source = os.path.join(outdir, f'Src/{machine}.cpp')

    gen_states_header(G, machine, fsm_header);
    gen_states_source(G, machine, entry, fsm_source);

def graph_events(G):
    events = set()
    labels = nx.get_edge_attributes(G, 'label')
    seen_edges = {}
    for e in nx.edges(G):
        if e not in seen_edges:
            seen_edges[e] = 0
        events.add(label2event(labels[e + (seen_edges[e],)]))
        seen_edges[e] += 1
    return events

def entry_states(G):
    entry = []
    labels = state_labels(G)
    for state in nx.nodes(G):
        if re.match('\(ENTRY\)', labels[state]):
            entry.append(state)
    
    return entry

def get_subgraph_from_entry(G, entry):
    tree = list(nx.algorithms.bfs_successors(G, entry))
    keys = list(map(lambda x: x[0], tree))
    vals = list(map(lambda x: x[1], tree))
    
    nodelist = keys
    for lst in vals:
        nodelist = nodelist + lst
    
    nodes = set()
    for node in nodelist:
        nodes.add(node)
    
    return G.subgraph(nodes)

def state_labels(G):
    return nx.get_node_attributes(G, 'label')

def label2event(label):
    label = label.strip()
    label = label.replace(" ", "_")
    result = re.match('\d+\(T(\d+)\)', label)
    if result:
        return 'TIMER_' + result.group(1) + '_EVENT'
    elif re.match('[a-zA-Z_]\w*', label):
        return label.upper() + '_EVENT'
    elif len(label) == 0:
        return 'UNCONDITIONAL'
    else:
        print(f'\nInvalid event name: {label}')
        exit(1)

def node_timer_events(G, node):
    labels = nx.get_edge_attributes(G, 'label')
    seen_edges = {}
    timers = set()
    for e in nx.edges(G, node):
        if e not in seen_edges:
            seen_edges[e] = 0
        timers.add(labels[e + (seen_edges[e],)])
        seen_edges[e] += 1
    timers = map(label2timer, timers)
    timers = filter(None, timers)
    return list(timers)

def label2timer(label):
    result = re.match('(\d+)\(T(\d+)\)', label)
    if result:
        return ('TIMER_' + result.group(2), result.group(1))
    else:
        return None

def event2timer(event):
    matches = re.match('(TIMER_\d+)_EVENT', event)
    if matches:
        return matches.group(1)
    else:
        return None

def node2state(node, machine):
    return f'{machine}_{node}'

def event2enum(event):
    return event + '_INDEX'

def header_comment():
    return '/* auto-generated by fsm_gen.py */\n'

def start_guard(guard):
    return f'#ifndef {guard}\n#define {guard}\n'

def end_guard(guard):
    return f'#endif /* {guard} */\n'

###############################################################################
#  Events.hpp Generation
###############################################################################

def gen_events_header(G, file):
    events = graph_events(G)
    guard = 'EVENTS_HPP_'

    with open(file, "w") as f:
        f.write(header_comment() + '\n')
        f.write(start_guard(guard) + '\n')
        f.write(events_includes() + '\n')
        if CODGEN:
            f.write(timer_typedef(events) + '\n')
            f.write(timer_prototypes() + '\n')
        f.write(base_event_definition() + '\n')
        for e in events:
            f.write(event_definition(e))
        f.write('\n' + end_guard(guard) + '\n')

def events_includes():
    return '#include "tinyfsm.hpp"\n'

def timer_typedef(events):
    events = map(event2timer, events)
    events = list(filter(None, events))
    
    typedef = 'typedef enum {\n'
    for i, e in enumerate(events):
        typedef += f'    {e} = {i},\n'
    typedef += f'    NUM_TIMERS = {len(events)}\n'
    typedef += '} Timer;\n'
    return typedef

def timer_prototypes():
    return ('/* TODO: Implement these functions in a user file! */\n'
            'void start_timer(Timer timer, int ms);\n'
            'void stop_timer(Timer timer);\n')

def base_event_definition():
    return 'struct BASE_EVENT : tinyfsm::Event {};\n'

def event_definition(event):
    return f'struct {event} : BASE_EVENT {{}};\n'

###############################################################################
#  user_states.cpp/hpp Generation
###############################################################################

def gen_user_states(G, source, header):
    states = list(G.nodes())
    guard = 'USER_STATES_HPP_'
    
    with open(source, "w") as f:
        f.write('#include "user_states.hpp"\n\n')
        f.write(user_states_functions(G, states))
    
    with open(header, "w") as f:
        f.write(start_guard(guard) + '\n')
        f.write(user_states_includes() + '\n')
        f.write(user_states_prototypes(states) + '\n')
        f.write(end_guard(guard) + '\n')

def user_states_functions(G, states):
    functions = ''
    labels = nx.get_node_attributes(G, 'label')
    
    for s in states:
        functions += f'/* {labels[s]} */\n'
        functions += (state_prototype(s) + ' {\n'
                      '    // TODO\n'
                      '}\n\n')
    
    return functions

def state_prototype(state):
    return f'void state_{state}(void)'

def user_states_includes():
    return ('#include "main.h"\n'
            '#include "Events.hpp"\n'
            '#include "fsm_fifo.hpp"\n')

def user_states_prototypes(states):
    protos = ''
    
    for s in states:
        protos += state_prototype(s) + ';\n'
    
    return protos

###############################################################################
#  fsm_fifo.cpp/hpp Generation
###############################################################################

def gen_fsm_fifo(G, source, header):
    events = graph_events(G)
    guard = 'FSM_FIFO_HPP_'
    
    with open(header, "w") as f:
        f.write(header_comment() + '\n')
        f.write(start_guard(guard) + '\n')
        f.write(fifo_includes() + '\n')
        f.write(fifo_event_enum(events) + '\n')
        f.write(fifo_struct() + '\n')
        f.write(fifo_prototypes() + '\n')
        f.write(end_guard(guard) + '\n')
    
    reference = os.path.join(Path(__file__).parent.absolute(), 'fsm_fifo.cpp')
    copyfile(reference, source, follow_symlinks=True)

def fifo_includes():
    return ('#include "Events.hpp"\n\n'
            '#define FIFO_SIZE 100\n')

def fifo_event_enum(events):
    code = 'typedef enum {\n'
    enums = list(map(lambda x: '    ' + event2enum(x), events))
    code += ',\n'.join(enums)
    code += '\n} FSM_Event;\n'
    
    return code

def fifo_struct():
    return ('typedef struct {\n'
            '    int head = 0;\n'
            '    int tail = 0;\n'
            '    FSM_Event buffer[FIFO_SIZE];\n'
            '} Event_FIFO;\n')

def fifo_prototypes():
    return ('void write_event(FSM_Event event);\n'
            'int read_event(FSM_Event *event);\n')

###############################################################################
#  fsm_driver.cpp/hpp Generation
###############################################################################

def gen_fsm_driver(G, source, header):
    events = graph_events(G)
    singletons = "".join(list(map(singleton_definition, events)))
    guard = 'FSM_DRIVER_HPP_'
    
    with open(header, "w") as f:
        f.write(header_comment() + '\n')
        f.write(start_guard(guard) + '\n')
        f.write(driver_prototype() + '\n')
        f.write(end_guard(guard) + '\n')
    
    with open(source, "w") as f:
        f.write(header_comment() + '\n')
        f.write(driver_includes(G) + '\n')
        f.write(fsm_list(G) + '\n')
        f.write(singletons + '\n')
        f.write(driver_function(events) + '\n')

def driver_prototype():
    return 'void start_fsm_driver();\n'

def driver_includes(G):
    inc =  '#include "fsm_driver.hpp"\n'
    inc += '#include "Events.hpp"\n'
    inc += '#include "fsm_fifo.hpp"\n'
    inc += '#include "tinyfsm.hpp"\n'
    inc += machine_includes(G)
    return inc

def machine_includes(G):
    inc = ''
    entries = entry_states(G)
    for i in range (0, len(entries)):
        inc += f'#include "FSM{i+1}.hpp"\n'
    
    return inc

def fsm_list(G):
    code = 'using my_fsm = tinyfsm::FsmList<'
    machines = []
    
    entries = entry_states(G)
    for i in range (0, len(entries)):
        machines.append(f'FSM{i+1}')
    code += ", ".join(machines)
    
    return code + '>;\n'

def event2singleton(event):
    return event + '_SINGLETON'

def singleton_definition(event):
    singleton = event2singleton(event)
    return f'{event} {singleton} = {event}();\n'

def event2case(event):
    enum = event2enum(event)
    singleton = event2singleton(event)
    return f'            case {enum}: my_fsm::dispatch({singleton});break;\n'

def driver_function(events):
    cases = "".join(list(map(event2case, events)))
    
    code =  ('void start_fsm_driver() {\n'
             '    FSM_Event event;\n\n'
             '    my_fsm::start();\n\n'
             '    while (1) {\n'
             '        if (read_event(&event)) {\n'
             '            switch (event) {\n')
    code += cases
    code += ('            }\n'
             '        }\n'
             '    }\n'
             '}\n')
    return code

###############################################################################
#  FSMx.hpp Generation
###############################################################################

def gen_states_header(G, machine, file):
    events = graph_events(G)
    guard = f'{machine}_HPP_'

    with open(file, "w") as f:
        f.write(header_comment() + '\n')
        f.write(start_guard(guard) + '\n')
        f.write(states_header_includes() + '\n')
        f.write(base_state_definition(machine, events) + '\n')
        f.write(end_guard(guard) + '\n')

def states_header_includes():
    return ('#include "Events.hpp"\n' 
            '#include "tinyfsm.hpp"\n'
            '#include "user_states.hpp"\n')

def base_state_definition(machine, events):
    base = (f'class {machine} : public tinyfsm::Fsm<{machine}> {{\n'
             'public:\n'
             '    void react(tinyfsm::Event const &) {};\n'
             '    virtual void entry(void) {};\n'
             '    virtual void exit(void) {};\n\n')
    for e in events:
        base += base_react(e)
    return base + '};\n'

def base_react(event):
    return f'    virtual void react({event} const &) {{}};\n'

###############################################################################
#  FSMx.cpp Generation
###############################################################################

def gen_states_source(G, machine, entry, file):
    with open(file, "w") as f:
        f.write(header_comment() + '\n')
        f.write(states_source_includes(machine) + '\n')
        f.write(forward_declarations(G, machine) + '\n')
        for s in G.nodes():
            f.write(state_definition(G, s, machine) + '\n')
        f.write(set_initial_state(G, machine, entry) + '\n')

def states_source_includes(machine):
    return f'#include "{machine}.hpp"\n'

def forward_declarations(G, machine):
    code = ''
    labels = nx.get_node_attributes(G, 'label')
    
    for s in G.nodes():
        name = node2state(s, machine)
        code += f'class {name};    /* {labels[s]} */\n'
    return code

def state_definition(G, node, machine):
    state_name = node2state(node, machine)
    
    code = (f'class {state_name} : public {machine} {{\n'
             '    void entry() {\n')
    
    code += start_timers(G, node)
    code += f'        {state_call(node)}\n'
    code += unconditional_transition(G, node, machine)
    code +=  '    }\n\n'
    
    code += react_definitions(G, node, machine)
    
    return code + '};\n'

def unconditional_transition(G, node, machine):
    labels = nx.get_edge_attributes(G, 'label')
    edges = list(nx.edges(G, node))
    if len(edges) == 1:
        e = edges[0]
        if label2event(labels[e + (0,)]) == 'UNCONDITIONAL':
            return f'        transit<{node2state(e[1], machine)}>();\n'
    return ''

def react_definitions(G, node, machine):
    labels = nx.get_edge_attributes(G, 'label')
    code = ''
    seen_edges = {}
    for e in nx.edges(G, node):
        if e not in seen_edges:
            seen_edges[e] = 0
        code += f'    void react({label2event(labels[e + (seen_edges[e],)])} const &) override {{\n'
        code += stop_timers(G, node)
        code += (f'        transit<{node2state(e[1], machine)}>();\n'
                  '    }\n\n')
        seen_edges[e] += 1
    
    return code[:-1]

def start_timers(G, node):
    timers = node_timer_events(G, node)
    code = ''
    
    if CODEGEN:
        for t in timers:
            code += f'        start_timer({t[0]}, {t[1]});\n'
    
    return code

def stop_timers(G, node):
    timers = node_timer_events(G, node)
    code = ''
    
    if CODEGEN:
        for t in timers:
            code += f'        stop_timer({t[0]});\n'
    
    return code

def set_initial_state(G, machine, entry):
    entry_state = node2state(entry, machine)
    return f'FSM_INITIAL_STATE({machine}, {entry_state});\n'

def state_call(state):
    return state_prototype(state).replace('void', '').strip() + ';'

###############################################################################
#  Main
###############################################################################

parser = argparse.ArgumentParser(description='Generate C++ state machine from dotfile graph.')
parser.add_argument('-s', '--stubs', action='store_true',
                    help=('forces stub generation even when this tool '
                          'would otherwise perform code generation.'))
parser.add_argument('infile', help='a *.dot file to be converted.')
parser.add_argument('outdir', help='directory to output generated code')

args = parser.parse_args()

if not os.path.exists(args.infile):
    print(f'Input file not found: {args.infile}')
    exit(1)

if not os.path.exists(args.outdir):
    os.makedirs(args.outdir)

inc = os.path.join(args.outdir, 'Inc')
if not os.path.exists(inc):
    os.makedirs(inc)

src = os.path.join(args.outdir, 'Src')
if not os.path.exists(src):
    os.makedirs(src)

CODGEN = not args.stubs

process_graph(args.infile, args.outdir)

