#define main benchmark_main
#include "benchmark/genetic_benchmark.cpp"
#undef main
#include <cassert>

// Node payloads identify candidates independently of the score. Check stable
// ties, NaNs converted to max(), infinities, and preservation of owned nodes.
int main() {
  std::mt19937 rng(598);
  for (int size : {0, 1, 2, 17, 512, 16384}) {
    std::vector<genetic::program> programs(size);
    std::vector<int> expected(size);
    std::vector<float> scores(size);
    std::iota(expected.begin(), expected.end(), 0);
    for (int i = 0; i < size; ++i) {
      programs[i].len = 1;
      programs[i].depth = i % 19;
      programs[i].nodes = new node[1]{node(static_cast<float>(i))};
      float score = static_cast<int>(rng() % 11) - 5.0f;
      if (i % 13 == 0) score = std::numeric_limits<float>::quiet_NaN();
      else if (i % 17 == 0) score = std::numeric_limits<float>::infinity();
      else if (i % 19 == 0) score = -std::numeric_limits<float>::infinity();
      else if (i % 23 == 0) score = std::numeric_limits<float>::max();
      programs[i].raw_fitness_ = score;
      scores[i] = std::isnan(score) ? std::numeric_limits<float>::max() : score;
    }
    // A total-order reference uses the initial ID to break equal-score ties.
    std::sort(expected.begin(), expected.end(), [&](int a, int b) {
      if (scores[a] == scores[b]) return a < b;
      return scores[a] < scores[b];
    });
    sortPrograms(programs.data(), size);
    for (int i = 0; i < size; ++i) {
      assert(programs[i].len == 1);
      assert(programs[i].depth == expected[i] % 19);
      assert(programs[i].nodes[0].u.val == expected[i]);
      assert(programs[i].raw_fitness_ == scores[expected[i]]);
    }
  }
}
