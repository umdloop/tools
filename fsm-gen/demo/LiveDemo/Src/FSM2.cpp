/* auto-generated by fsm_gen.py */

#include "FSM2.hpp"

class FSM2_S03;    /* (ENTRY)Three */
class FSM2_S04;    /* Four */

class FSM2_S03 : public FSM2 {
    void entry() {
        start_timer(TIMER_2, 500);
        state_S03();
    }

    void react(TIMER_2_EVENT const &) override {
        stop_timer(TIMER_2);
        transit<FSM2_S04>();
    }
};

class FSM2_S04 : public FSM2 {
    void entry() {
        start_timer(TIMER_2, 500);
        state_S04();
    }

    void react(TIMER_2_EVENT const &) override {
        stop_timer(TIMER_2);
        transit<FSM2_S03>();
    }
};

FSM_INITIAL_STATE(FSM2, FSM2_S03);

