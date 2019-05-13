import multiprocessing as mp

from tests.test_minas_fake import MinasFakeExamplesTest
from tests.run import runConcurrent

def fake_seed(seed):
    t = MinasFakeExamplesTest()
    t.setUpClass()
    t.setUp()
    return t.fake_seed(seed)

if __name__ == '__main__':
    runConcurrent()
    # cpu_count = 4
    # try:
    #     cpu_count = mp.cpu_count()
    # except:
    #     pass
    # with mp.Pool(cpu_count) as pool:
    #     for i in pool.map(fake_seed, [200, 201, 202]):
    #         print('\n', i)
