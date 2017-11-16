from timeit import default_timer as timer

from vectorbt import strategy, positions
from vectorbt.optimizer.gridsearch import params


##########
### L1 ###
##########

# Random
########

def random(rate_sr, n, N):
    """
    Generate random positions N times

    :param maxn: max number of positions in vector
    :param N: number of vectors in the map
    :return: position series keyed by their index
    """

    def positions_func():
        entries = strategy.random_entry_vector(rate_sr, n)
        exits = strategy.random_exit_vector(rate_sr, entries, n)
        pos_sr = positions.from_vectors(rate_sr, entries, exits)
        return pos_sr

    print("random-posmap")
    print("setup: positions = ~%d, N = %d" % (n, N))
    t1 = timer()
    positions_func()
    t2 = timer()
    print("calcs: %d (~%.2fs)" % (N, N * (t2 - t1)))
    posmap = dict(zip(range(N), params.repeat(positions_func, N)))
    print("passed. %.2fs" % (timer() - t1))
    return posmap


# Moving averages
#################

def ma(rate_sr, min_ma, max_ma, step, th, ma_func):
    """
    Generate crossover positions for a range of MA windows combinations

    :param min_ma: minimum window for MA
    :param max_ma: maximum window
    :param step: step
    :param th: threshold (filter) for crossover in % of current rate
    :param ma_func: either SMA or EMA
    :return: position series keyed by windows
    """
    # Precalculation
    params_range = params.range_params(min_ma, max_ma, step)
    mas = params.onemap(lambda x: ma_func(rate_sr, x), params_range)

    # Calculation
    def positions_func(fast_ma, slow_ma):
        entries = strategy.ma_entry_vector(rate_sr, mas[fast_ma], mas[slow_ma], th=th)
        exits = strategy.ma_exit_vector(rate_sr, mas[fast_ma], mas[slow_ma], th=th)
        pos_sr = positions.from_vectors(rate_sr, entries, exits)
        return pos_sr

    print("ma-posmap")
    print("setup: ma_func = %s, th = %s" % (ma_func.__name__, str(th)))
    p = params.combine_rep_params(min_ma, max_ma, step, 2)
    print("grid: %f -> %f = %d" % (min_ma, max_ma, len(p)))
    t1 = timer()
    positions_func(min_ma, max_ma)
    t2 = timer()
    print("calcs: %d (~%.2fs)" % (len(p), len(p) * (t2 - t1)))
    # Window of fast MA is lower or equal than of slow MA
    posmap = params.starmap(positions_func, p)
    print("passed. %.2fs" % (timer() - t2))
    return posmap


def math(rate_sr, fast_ma, slow_ma, ma_func, min_th, max_th, step):
    """
    Generate crossover positions for a range of threshold combinations

    :param fast_ma: window of fast MA
    :param slow_ma: window of slow MA
    :param ma_func: either SMA or EMA
    :param min_th: minimum threshold
    :param max_th: maximum threshold
    :param step: step
    :return: position series keyed by thresholds
    """
    # Precalculation
    fast_ma_sr = ma_func(rate_sr, fast_ma)
    slow_ma_sr = ma_func(rate_sr, slow_ma)

    # Calculation
    def positions_func(th_x, th_y):
        entries = strategy.ma_entry_vector(rate_sr, fast_ma_sr, slow_ma_sr, th=(th_x, th_y))
        exits = strategy.ma_exit_vector(rate_sr, fast_ma_sr, slow_ma_sr, th=(th_x, th_y))
        pos_sr = positions.from_vectors(rate_sr, entries, exits)
        return pos_sr

    print("math-posmap")
    print("setup: ma_func = %s (%d, %d)" % (ma_func.__name__, fast_ma, slow_ma))
    p = params.product_params(min_th, max_th, step, 2)
    print("grid: %f -> %f = %d" % (min_th, max_th, len(p)))
    t1 = timer()
    positions_func(min_th, max_th)
    t2 = timer()
    print("calcs: %d (~%.2fs)" % (len(p), len(p) * (t2 - t1)))
    # Window of fast MA is lower or equal than of slow MA
    posmap = params.starmap(positions_func, p)
    print("passed. %.2fs" % (timer() - t2))
    return posmap
