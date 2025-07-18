import os
import sys
import logging
from simple_app import app

if __name__ == '__main__':
    logging.info("Starting APK Editor application via run_app.py")
    
    # Fix for duplicate route definitions
    # This will ensure that only the first definition of each route is used
    for rule in app.url_map.iter_rules():
        endpoint = rule.endpoint
        view_func = app.view_functions[endpoint]
        # Make sure each endpoint has only one route
        for other_rule in app.url_map.iter_rules():
            if other_rule != rule and other_rule.endpoint == endpoint:
                app.url_map._rules.remove(other_rule)
    
    app.run(debug=True, host='0.0.0.0', port=5000)