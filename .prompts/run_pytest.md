## Tasks

- You will be generating a `pytest` function that tests the execution of the given function. This function will be pasted in your context window.
- You are to write a comprehensive test that tests the main use cases of the function,
and also tests the edge cases of the function.
- You are to follow the Pytest Guidelines procided below.

## Pytest Guidelines
There are 6 main rules that you NEED to follow when writing tests. These rules are:

1. ### Simple Test

Test one feature at a time

- Small test
- A single assertion

Example code

```python
def some_calculation(a, b):
    return a + b

def make_a_dict(a, b):
    if a < 0 or b < 0:
        raise ValueError("a and b must be positive")

    operation = some_calculation(a, b)

    return {"a": a, "b": b, "result": operation}
```

🚨 Bad

```python
def test_dict():
    assert make_a_dict(2, 3) == {"a": 2, "b": 3, "result": 5}
    with pytest.raises(ValueError):
         make_a_dict(-1, -1)
```

✅ Good

```python
def test_make_a_dict():
    """
    Test the make_a_dict function to ensure it returns the expected dictionary.
    """
    my_dict = make_a_dict(2, 3)

    expected_dict = {"a": 2, "b": 3, "result": 5}

    assert my_dict == expected_dict


def test_make_a_dict_with_negative_values():
    """
    Test that make_a_dict raises a ValueError when negative values are passed.
    """
    with pytest.raises(ValueError):
        make_a_dict(-1, -1)
```

2. ### Mock everything we don’t want to test

- isolate functions from other functions
Example code

```python
def some_calculation(a, b):
    return a + b

def make_a_dict(a, b):
    if a < 0 or b < 0:
        raise ValueError("a and b must be positive")

    operation = some_calculation(a, b)

    return {"a": a, "b": b, "result": operation}
```

🚨 Bad

```python
def test_make_a_dict():
    """
    Test the make_a_dict function to ensure it returns the expected dictionary.
    """
    my_dict = make_a_dict(2, 3)

    expected_dict = {"a": 2, "b": 3, "result": 5}

    assert my_dict == expected_dict
```

✅ Good

```python
def test_make_a_dict(mocker):
    """
    Test the make_a_dict function to ensure it returns the expected dictionary.
    """
    mocker.patch(
        "__main__.some_calculation",
        return_value=5,
        autospec=True
    )

    my_dict = make_a_dict(2, 3)

    expected_dict = {"a": 2, "b": 3, "result": 5}

    assert my_dict == expected_dict

def test_some_calculation():
    """
    Test the some_calculation function to ensure it returns the expected value.
    """
    value = some_calculation(2, 3)

    expected_value = 5

    assert value == expected_value
```

3. ### DRY (Don’t repeat yourself)

- 🔥 parametrize

```python
def add_numbers(a, b):
    return a + b

@pytest.mark.parametrize("a, b, expected_result", [
    (2, 3, 5),
    (-10, 5, -5),
    (0, 0, 0),
    (100, -50, 50)
])
def test_add_numbers(a, b, expected_result):
    result = add_numbers(a, b)
    assert result == expected_result
```

- 🔥 fixture

```python
class Person:
    def __init__(self, name):
        self.name = name
        self.age = 0

    def is_adult(self):
        return self.age >= 18
```

🚨 Bad

```python
def test_person_is_adult(person):
    person = Person("Emi")
    person.age = 19
    assert person.is_adult()

def test_person_is_not_adult(person):
    person = Person("Emi")
    person.age = 10
    assert not person.is_adult()
```

✅ Good

```python
@pytest.fixture
def person():
    person = Person("Emi")
    return person

def test_person_is_adult(person):
    person.age = 19
    assert person.is_adult()

def test_person_is_not_adult(person):
    person.age = 10
    assert not person.is_adult()
```

4. ### Test behavior, not implementation

Example code

```python
from dataclasses import dataclass

@dataclass
class User:
    username: str

class InMemoryUserRepository:
    def __init__(self):
        self._users = []

    def add(self, user):
        self._users.append(user)

    def get_by_username(self, username):
        return next(user for user in self._users if user.username == username)
```

🚨 Bad

```python
def test_add():
    user = User(username="johndoe")
    repository = InMemoryUserRepository()
    repository.add(user)

    assert user in repository._users

def test_get_by_username():
    user = User(username="johndoe")
    repository = InMemoryUserRepository()
    repository._users = [user]

    user_from_repository = repository.get_by_username(user.username)

    assert user_from_repository == user
```

✅ Good

```python
def test_added_user_can_be_retrieved_by_username():
    user = User(username="johndoe")
    repository = InMemoryUserRepository()
    repository.add(user)

    assert user == repository.get_by_username(user.username) 
```

5. ### Do not test the framework (at least in unit tests)
🚨 Bad
```python
from django.contrib.auth.models import User

@pytest.mark.django_db
def test_django_authentication():
    user = User.objects.create_user(username='testuser', password='testpassword')
    authenticated = user.check_password('testpassword')
    assert authenticated
from flask import Flask

def test_flask_error_handling():
    app = Flask(__name__)

    with app.test_client() as client:
        response = client.get('/nonexistent-route')
        assert response.status_code == 404
        assert 'Not Found' in response.get_data(as_text=True)
```
6. ### Autospect True
This is useful when you want to verify or inspect specific features of a function or method during testing. For example, Autospec True can be used to check if a function is called with the correct arguments, if it returns the expected values, or if the appropriate methods of an object are called.

Example code
```python
def some_calculation(a, b):
    return a + b

def make_a_dict(a, b):
    if a < 0 or b < 0:
        raise ValueError("a and b must be positive")

    operation = some_calculation(a, b)

    return {"a": a, "b": b, "result": operation}
```
✅ Good
```python
def test_make_a_dict(mocker):
    """
    Test the make_a_dict function to ensure it returns the expected dictionary.
    """
    mocker.patch(
        "__main__.some_calculation",
        return_value=5,
        autospec=True
    )

    my_dict = make_a_dict(2, 3)

    expected_dict = {"a": 2, "b": 3, "result": 5}

    assert my_dict == expected_dict
```
