import pytest


# Step 1: Function to create a list of objects
def create_objects():
    return [True, False, True]

# Step 2: Parametrized test function
@pytest.mark.parametrize("obj", create_objects())
def test_function(obj):
    # Your test code here
    assert obj
