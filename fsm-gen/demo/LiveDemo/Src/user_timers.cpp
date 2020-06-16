#include "main.h"
#include "Events.hpp"
#include "fsm_fifo.hpp"

static void start_hal_timer(TIM_HandleTypeDef htim, int ms);
static void stop_hal_timer(TIM_HandleTypeDef htim);

extern int timer1;

extern TIM_HandleTypeDef htim1;
extern TIM_HandleTypeDef htim2;
extern TIM_HandleTypeDef htim3;

void start_timer(Timer timer, int ms) {
	switch (timer) {
	case TIMER_1: start_hal_timer(htim1, ms);return;
	case TIMER_2: start_hal_timer(htim2, ms);return;
	case TIMER_3: start_hal_timer(htim3, ms);return;
	case NUM_TIMERS: return;
	}
}

static void start_hal_timer(TIM_HandleTypeDef htim, int ms) {
	htim.Init.Period = 10*ms;
	HAL_TIM_Base_Init(&htim);
	__HAL_TIM_CLEAR_IT(&htim, TIM_IT_UPDATE);
	HAL_TIM_Base_Start_IT(&htim);
}

void stop_timer(Timer timer) {
	switch (timer) {
	case TIMER_1: stop_hal_timer(htim1);return;
	case TIMER_2: stop_hal_timer(htim2);return;
	case TIMER_3: stop_hal_timer(htim3);return;
	case NUM_TIMERS: return;
	}
}

static void stop_hal_timer(TIM_HandleTypeDef htim) {
	HAL_TIM_Base_Stop_IT(&htim);
	__HAL_TIM_SET_COUNTER(&htim, 0);
}

void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim) {
	switch ((uint32_t)htim->Instance) {
	case (uint32_t)TIM1_BASE: write_event(TIMER_1_EVENT_INDEX);return;
	case (uint32_t)TIM2_BASE: write_event(TIMER_2_EVENT_INDEX);return;
	case (uint32_t)TIM3_BASE: write_event(TIMER_3_EVENT_INDEX);return;
	}
}
