#Other imports
import re

from cdk.utils import (
    sanitize_name
)

from cdk.configuration.configuration import (
    load_configuration
)
# Because we are referencing existing resources, we require pulling the configuration for performing the tests
deploy_env = "development" 

conf = load_configuration("../config/{0}.yaml".format(deploy_env))


################ APP NAME SANITATION FUNCTION TESTS ##################

def test_all_lowercase():
    
    app_name = sanitize_name(conf.app_name)

    assert app_name.islower()

def test_symbol_removal():

    app_name = sanitize_name(conf.app_name)

    #Test passes as long as the only symbols in the name are hyphens or underscores
    assert not(re.search('[^0-9a-zA-Z-_]+', app_name))

def test_hyphen_replacement():

    app_name = sanitize_name(conf.app_name)

    #Passes if no underscores are found
    assert re.search('[^_]+', app_name)


def test_consecutive_hyphens():

    app_name = sanitize_name(conf.app_name)

    #Passes the test if there aren't more than one consecutive hyphen
    assert not(re.search('-{2,}',app_name))

def test_max_length():

    app_name = sanitize_name(conf.app_name)
    max_length = 40

    #Length of app_name is has to be equal or less than a maximium length
    assert len(app_name) <= max_length
