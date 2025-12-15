import atexit
from functools import wraps
from inspect import getfullargspec

from utils import blue, red, green, magenta

from project import (
    gen_solution, find_duration
)

pos_success = 0
pos_fail    = 0
neg_success = 0
neg_fail    = 0


def log_tests():
    tot = pos_success + pos_fail + neg_success + neg_fail
    if tot == 0:
        return
    print('')
    if neg_fail == 0:
        print(green('\tNo negative test failed!'))
    else:
        print(red(f'\t{neg_fail} negative tests failed!'))
    if pos_fail == 0:
        print(green('\tNo positive test failed!'))
    else:
        print(red(f'\t{pos_fail} positive tests failed!'))


def test_function(fct):
    @wraps(fct)
    def wrapper(*args, **kwargs):
        name = fct.__name__.ljust(15)
        marker = blue('='*10)
        print(marker, 'Entering test function:', name, marker)
        fct(*args, *kwargs)
        print(marker, 'Exiting test function: ', name, marker, end='\n\n')
    return wrapper


def throw(msg, prefix=''):
    if prefix:
        msg = prefix + ' ' + msg
    raise ValueError(msg)


def verify(solution, durations, c, T):
    n = len(durations)
    A = [True] * len(durations)
    B = [False] * len(durations)
    in_A = True
    for i in range(len(solution)):
        t, moving = solution[i]
        if i+1 < len(solution):
            delta_t = solution[i+1][0] - t
        else:
            delta_t = T - t
        ref = A if in_A else B
        prefix = f'[At time {t=}]'
        if t >= T:
            throw(f'Cannot move: after given duration ({T=})', prefix)
        for idx in moving:
            if not ref[idx-1]:
                throw(f'Chick {idx} cannot move', prefix)
            A[idx-1] = not A[idx-1]
            B[idx-1] = not B[idx-1]
        for idx in moving:
            if durations[idx-1] > delta_t:
                throw(
                    f'Chick {idx} needs {durations[idx-1]}s to cross '
                    f'but it only took {delta_t}s',
                    prefix
                )
        in_A = not in_A
    if not all(B):
        throw(f'Chicks{[j for j in range(1, n+1) if not B[j-1]]} not on B side')


def _verify_size(solution, durations, c, T):
    if solution != T:
        throw(f'Expected {T} but got {solution}')


def test_positive(caller, callback, instances, check_callback=verify):
    global pos_success, pos_fail
    nb_args = len(getfullargspec(callback).args)
    for counter, args in enumerate(instances, start=1):
        prefix = (f'[{caller}+:Test {counter}]').ljust(20)
        solution = callback(*args[:nb_args])
        if solution is None:
            print(f'\t{prefix} Test {red("failed")}: no solution found')
            pos_fail += 1
            continue
        try:
            check_callback(solution, *args)
        except ValueError as e:
            print(f'\t{prefix} Test {red("failed")}: {str(e)}')
            pos_fail += 1
        else:
            print(f'\t{prefix} Test {green("passed")}')
            pos_success += 1


def test_negative(caller, callback, instances):
    global neg_success, neg_fail
    nb_args = len(getfullargspec(callback).args)
    for counter, args in enumerate(instances, start=1):
        prefix = (f'[{caller}-:Test {counter}]').ljust(20)
        solution = callback(*args[:nb_args])
        if solution is None:
            print(f'\t{prefix} Test {green("passed")}')
            neg_success += 1
        else:
            print(f'\t{prefix} Test {red("failed")}')
            neg_fail += 1

########## Define test functions here below


def test_basic_Q2():
    # (durations, c, T)
    BASIC_INSTANCE = [
        ([1, 3, 6, 8], 2, 18)
    ]
    test_positive('test_basic_Q2', gen_solution, BASIC_INSTANCE)


def test_basic_Q3():
    BASIC_INSTANCE = [
        ([1, 3, 6, 8], 2, 18)
    ]
    test_positive('test_basic_Q3', find_duration, BASIC_INSTANCE, _verify_size)


SMALL_INSTANCES = [
    ([1, 1], 2, 1),
    ([1, 1, 1, 1], 4, 1),
    ([1, 1, 1, 1], 2, 5),
    ([2, 3, 4], 2, 9),
    ([1, 2, 5, 10], 2, 17),
    ([1, 4, 10, 12, 5], 2, 31)
]


def test_small_Q2():
    SMALL_INSTANCES_POS = SMALL_INSTANCES
    SMALL_INSTANCES_NEG = [
        ([1, 1, 1, 1], 3, 1),
        ([1, 1, 1, 1], 2, 4),
        ([2, 3, 4], 2, 8),
        ([1, 2, 5, 10], 2, 16),
        ([1, 4, 10, 12, 5], 2, 15),
        ([1, 4, 10, 12, 5], 2, 30)
    ]
    test_positive('test_small', gen_solution, SMALL_INSTANCES_POS)
    test_negative('test_small', gen_solution, SMALL_INSTANCES_NEG)


def test_small_Q3():
    test_positive('test_small', find_duration, SMALL_INSTANCES, _verify_size)


BIG_INSTANCES = [
    ([1, 3, 6, 8, 2, 10, 4, 12, 15], 2, 52),
]


def test_big_Q2():
    BIG_INSTANCES_POS = BIG_INSTANCES
    BIG_INSTANCES_NEG = [
        ([1, 3, 6, 8, 2, 10, 4, 12, 15], 2, 26),
        ([1, 3, 6, 8, 2, 10, 4, 12, 15], 2, 51),
    ]
    test_positive('test_big', gen_solution, BIG_INSTANCES_POS)
    test_negative('test_big', gen_solution, BIG_INSTANCES_NEG)


def test_big_Q3():
    test_positive('test_big', find_duration, BIG_INSTANCES, _verify_size)

########## Define test functions here above


# ``Auto decorate'' test functions
_keys = [
    k
    for k in globals()
    if k.startswith('test_') and k not in (
        'test_function', 'test_positive', 'test_negative'
    )
]
for _name in _keys:
    if _name.startswith('test_'):
        globals()[_name] = test_function(globals()[_name])


def main():
    print(magenta('\n   ##########   Tests for Q2  ##########   \n'))
    test_basic_Q2()
    test_small_Q2()
    test_big_Q2()
    print(magenta('\n   ##########   Tests for Q3  ##########   \n'))
    test_basic_Q3()
    test_small_Q3()
    test_big_Q3()


if __name__ == '__main__':
    atexit.register(log_tests)
    main()
