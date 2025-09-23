format_rules = {
    'Lifestyle': {
        'mode': 'map',
        'factors': {
            'Work': {'None': 0, 'Little': 1, 'Moderate': 2, 'A lot': 3},
            'Stress': {'None': 0, 'Little': 1, 'Moderate': 2, 'A lot': 3},
            'Time Outside': {'None': 0, 'Little': 1, 'Moderate': 2, 'A lot': 3},
            'Screen Time': {'None': 0, 'Little': 1, 'Moderate': 2, 'A lot': 3},
        }
    },
    'Active': {
        'mode': 'map',
        'factors': {
            'Activity level': {'None': 0, 'Low': 1, 'Moderate': 2, 'High': 3},
        }
    },
    'Social': {
        'mode': 'map',
        'factors': {
            'Sociability level': {'None': 0, 'Little': 1, 'Moderate': 2, 'A lot': 3},
            'Social interaction quality': {'Poor': 1, 'OK': 2, 'Good': 3},
        }
    },
    'Weather': {
        'mode': 'map',
        'factors': {
            'Active level': {'None': 0, 'Low': 1, 'Moderate': 2, 'High': 3},
        }
    },
    'Creative': {
        'mode': 'map',
        'factors': {}
    },    
    'Symptom': {
        'mode': 'symptom',
        'factors': {}
    },
    'Sleep': {
        'mode': 'map',
        'factors': {}
    },
    'Sleep quality': {
        'mode': 'energy_mood',
        'factors': {
        }
    },
    'Nutrition': {
        'mode': 'map',
        'factors': {
            'Sugar': {'Little': 1, 'Moderate': 2, 'A Lot': 3},
            'Protein': {'Little': 1, 'Moderate': 2, 'A Lot': 3},
        }
    },
    'Mood': {
        'mode': 'energy_mood',
        'factors': {}
    },
    'Energy': {
        'mode': 'energy_mood',
        'factors': {}
    },
    'Heart Measurements': {
        'mode': 'remove',
        'factors': {}
    },
    'Med/Supplements': {
        'mode': 'preserve',
        'factors': {}
    },
    'Bowel Movements': {
        'mode': 'count_retain',
        'factors': {}
    },
    'Gratitudes': {
        'mode':'remove',
        'factors': {}
    }
}

__all__ = ['format_rules']