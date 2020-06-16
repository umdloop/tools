#include "fsm_fifo.hpp"
#include "Events.hpp"

Event_FIFO fifo;

/* This function writes one event to the fifo buffer.
 *
 * Params:
 *   FSM_Event event -> event to be stored in the fifo
 *
 * Returns:
 *   void
 */
void write_event(FSM_Event event) {
	int next = fifo.tail + 1;

	if ((next == fifo.head) || ((next == FIFO_SIZE) && (fifo.head == 0))) {
		/* Buffer is full! */
	} else {
		/* Write event to end of buffer */
		fifo.buffer[fifo.tail] = event;
		fifo.tail = (fifo.tail == (FIFO_SIZE - 1)) ? 0 : next;
	}
}

/* This function reads one event from the fifo buffer.
 *
 * Params:
 *   FSM_Event *event -> location to put event
 *
 * Returns:
 *   0 -> nothing to read, event should be ignored
 *   1 -> success, event updated
 */
int read_event(FSM_Event *event) {
	if (fifo.head == fifo.tail) {
		/* Buffer is empty! */
		return 0;
	} else {
		*event = fifo.buffer[fifo.head];
		fifo.head = (fifo.head == (FIFO_SIZE - 1)) ? 0 : fifo.head + 1;
		return 1;
	}
}
