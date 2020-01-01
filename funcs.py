import numpy as np
import random
import itertools
from inspect import signature
import pretty_midi

def normalize(array):
    array = np.array(array)
    return array / sum(array)

def get_partition(n):
    """Gets the partition"""
    a = [0 for i in range(n + 1)]
    k = 1
    y = n - 1
    while k != 0:
            x = a[(k - 1)] + 1
            k -= 1
            while 2 * x <= y:
                    a[k] = x
                    y -= x
                    k += 1
            l = k + 1
            while x <= y:
                    a[k] = x
                    a[l] = y
                    yield a[:k + 2]
                    x += 1
                    y -= 1
            a[k] = x + y
            y = x + y - 1
            yield a[:k + 1]

def select_partition(n, type = 'equal', one_allowed='yes'):
    partition = list(get_partition(n))
    if one_allowed == 'no':
        partition = partition[:-1]
    if np.shape(partition) == (1,1): return partition[0]
    if type == 'equal':
        # print(np.shape(partition))
        return np.random.choice(partition)
    elif type == 'rounded':
        p = normalize([1 / len(i) for i in partition])
        return np.random.choice(partition, p = p)
    # choice = np.random.randint(0, len(p))
    # return p[choice]


def dc_alg(choices, epochs, alpha=1.0, weights=0, counts=0, verbosity=0):
    selections = []
    if np.all(counts == 0):
        counts = [
         1] * len(choices)
    weights = np.array(weights)
    if np.all(weights) == 0:
        weights = [
         1] * len(choices)
    for q in range(epochs):
        sum_ = sum([weights[i] * counts[i] ** alpha for i in range(len(choices))])
        probs = [weights[i] * counts[i] ** alpha / sum_ for i in range(len(choices))]
        selection_index = np.random.choice((list(range(len(choices)))), p=probs)
        counts = [i + 1 for i in counts]
        counts[selection_index] = 0
        selections.append(choices[selection_index])

    selections = np.array(selections)
    counts = np.array(counts)
    if verbosity == 0:
        return selections
    if verbosity == 1:
        return (
         selections, counts)

def normal_distribution_maker(bins):
    distribution = np.random.normal(size=100000)
    distribution = np.histogram(distribution, bins=bins, density=True)[0]
    distribution /= np.sum(distribution)
    return distribution

def nPVI(d):
    m = len(d)
    return 100 / (m - 1) * sum([abs((d[i] - d[(i + 1)]) / (d[i] + d[(i + 1)]) / 2) for i in range(m - 1)])

def nPVI_averager(window_width, durs):
    return [nPVI(durs[i:i + window_width]) for i in range(len(durs) - window_width)]

def nCVI(d):
    matrix = [list(i) for i in itertools.combinations(d, 2)]
    matrix = [nPVI(i) for i in matrix]
    return sum(matrix) / len(matrix)

def segment(num_of_segments,nCVI_average,factor=2.0):
    section_durs = factor ** np.random.normal(size=2)
    while abs(nCVI(section_durs) - nCVI_average) > 1.0:
        section_durs = factor ** np.random.normal(size=2)
    for i in range(num_of_segments - 2):
        next_section_durs = np.append(section_durs,[factor ** np.random.normal()])
        ct=0
        while abs(nCVI(next_section_durs) - nCVI_average) > 1.0:
            ct+=1
            next_section_durs = np.append(section_durs, [factor ** np.random.normal()])
        section_durs = next_section_durs
        # print(ct)
    section_durs /= np.sum(section_durs)
    return section_durs

def auto_args(target):
    """
    A decorator for automatically copying constructor arguments to `self`.
    """
    # Get a signature object for the target method:
    sig = signature(target)
    def replacement(self, *args, **kwargs):
        # Parse the provided arguments using the target's signature:
        bound_args = sig.bind(self, *args, **kwargs)
        # Save away the arguments on `self`:
        for k, v in bound_args.arguments.items():
            if k != 'self':
                setattr(self, k, v)
        # Call the actual constructor for anything else:
        target(self, *args, **kwargs)
    return replacement

def spread(init, max_ratio):
    exponent = np.clip(np.random.normal() / 3, -1, 1)
    return init * (max_ratio ** exponent)

def dc_alg(choices, epochs, alpha=1.0, weights=0, counts=0, verbosity=0):
    selections = []
    if np.all(counts == 0):
        counts = [
         1] * len(choices)
    weights = np.array(weights)
    if np.all(weights) == 0:
        weights = [
         1] * len(choices)
    for q in range(epochs):
        sum_ = sum([weights[i] * counts[i] ** alpha for i in range(len(choices))])
        probs = [weights[i] * counts[i] ** alpha / sum_ for i in range(len(choices))]
        selection_index = np.random.choice((list(range(len(choices)))), p=probs)
        counts = [i + 1 for i in counts]
        counts[selection_index] = 0
        selections.append(choices[selection_index])
    selections = np.array(selections)
    counts = np.array(counts)
    if verbosity == 0:
        return selections
    if verbosity == 1:
        return (
         selections, counts)

def dc_weight_finder(choices, alpha, weights, test_epochs=500):
    choices = np.arange(len(choices))
    weights_ = [i / sum(weights) for i in weights]
    max_off = .051
    # cts_ = 0
    test_ct = 0
    while max_off > 0.05:
        test_ct += 1
        if (test_ct > 1000) and (test_ct%100 == 0): print(test_ct)

        # print(cts_)
        y = dc_alg(choices, test_epochs, alpha, weights)
        #this should be rewritten as a np function
        results = np.array([np.count_nonzero(y==choices[i]) / test_epochs for i in choices])
        results = np.where(results == 0, results, 0.001)
        diff = weights_ / results
        weights *= diff
        weights /= sum(weights)
        max_off = np.max(1 - diff)
        # print(max_off)
        # cts_+=1
        # print(cts_)
    return weights

def weighted_dc_alg(choices, epochs, alpha=1.0, weights=0, counts=0, verbosity=0, weights_dict={}):
    if np.any(weights) != 0:
        # this basically says if its not going to work, just double the length
        #of the choice array, and try again. Might be better to just double the
        # one value thats above 0.5 . Or, might make more sense to just do a straight
        # random choice.
        if np.max(weights) >= 0.5:
            choices = np.tile(choices, 2)
            weights = np.tile(weights/2, 2)
            counts = np.tile(counts, 2)

        #if there are any weights that are 0, this will just remove that item
        #from the weights and from the choices, so dc_weight_finder doesn't break
        nonzero_locs = np.nonzero(weights != 0)
        choices = choices[nonzero_locs]
        weights = weights[nonzero_locs]
        weights = dc_weight_finder(choices, alpha, weights)
    selections = dc_alg(choices, epochs, alpha, weights, counts, verbosity)
    return selections


def print_progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█', printEnd='\r'):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "
", "
") (Str)
    """
    percent = ('{0:.' + str(decimals) + 'f}').format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix)), end=printEnd)
    if iteration == total:
        print()

def easy_midi_generator(notes, file_name, midi_inst_name):
    notes = sorted(notes, key=(lambda x: x[1]))
    score = pretty_midi.PrettyMIDI()
    instrument_program = pretty_midi.instrument_name_to_program(midi_inst_name)
    instrument = pretty_midi.Instrument(program=0)
    for n, note in enumerate(notes):
        if type(note[3]) == np.float64:
            vel = np.int(np.round(127 * note[3]))
        elif type(note[3]) == float:
            vel = np.int(np.round(127 * note[3]))
        elif type(note[3]) == int:
            vel = note[3]
        else: print(note[3])
        note = pretty_midi.Note(velocity=vel, pitch=(note[0]), start=(note[1]), end=(note[1] + note[2]))
        instrument.notes.append(note)
    score.instruments.append(instrument)
    score.write(file_name)
