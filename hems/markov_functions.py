import numpy as np

def generate_markov_chain(min_soc, cd_rate, morning_prob, midday_prob, afternoon_prob, night_prob):
    initial_state = 0
    availability = 48
    markov_availability = np.zeros(availability)
    markov_availability[:2] = initial_state

    min_charge = np.ones(availability)

    for i in range(2, availability):
        current_state = int(markov_availability[i-1])
        trans_prob = night_prob[current_state, :]  # Default to night time

        if 11 <= i <= 21:
            trans_prob = morning_prob[current_state, :]
        elif 21 < i <= 29:
            trans_prob = midday_prob[current_state, :]
        elif 29 < i <= 39:
            trans_prob = afternoon_prob[current_state, :]

        next_state = np.random.choice([0, 1], p=trans_prob)
        markov_availability[i] = next_state

    markov_availability[markov_availability == 1] = 0
    markov_availability *= cd_rate

    first_leave = np.argmax(markov_availability == 0)
    if first_leave > 0:
        min_charge[first_leave-2:first_leave] = min_soc

    return markov_availability, min_charge

def markov_weekday(min_soc, cd_rate):
    morning_prob = np.array([[0.1, 0.9], [0.1, 0.95]])
    midday_prob = np.array([[0.6, 0.4], [0.3, 0.7]])
    afternoon_prob = np.array([[0.8, 0.2], [0.8, 0.2]])
    night_prob = np.array([[0.98, 0.02], [0.8, 0.2]])

    return generate_markov_chain(min_soc, cd_rate, morning_prob, midday_prob, afternoon_prob, night_prob)

def markov_weekend(min_soc, cd_rate):
    morning_prob = np.array([[0.7, 0.3], [0.1, 0.9]])
    midday_prob = np.array([[0.4, 0.6], [0.3, 0.7]])
    afternoon_prob = np.array([[0.8, 0.2], [0.8, 0.2]])
    night_prob = np.array([[0.98, 0.02], [0.8, 0.2]])

    return generate_markov_chain(min_soc, cd_rate, morning_prob, midday_prob, afternoon_prob, night_prob)
