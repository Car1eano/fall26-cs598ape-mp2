#include "custom_distributions.h"
#include <cassert>
#include <random>
#include <utility>
#include <vector>

// This reference expresses the old VM's range arithmetic as defined unsigned
// arithmetic. Check both outputs and engine consumption for the used ranges.
int reference(std::mt19937 &rng, int low, int high) {
  const uint32_t range = static_cast<uint32_t>(high) - static_cast<uint32_t>(low) + 1u;
  const uint32_t limit = UINT32_MAX - UINT32_MAX % range;
  uint32_t value;
  do value = rng(); while (value >= limit);
  return static_cast<int>(static_cast<int64_t>(low) + value % range);
}

int main() {
  const int maximum = std::numeric_limits<int>::max();
  uniform_int_distribution_custom<int> default_distribution;
  std::mt19937 default_rng(598), default_reference(598);
  for (int i = 0; i < 10000; ++i) {
    assert(default_distribution(default_rng) == reference(default_reference, 0, maximum));
  }
  assert(default_rng() == default_reference());
  for (auto bounds : std::vector<std::pair<int, int>>{
      {0, 0}, {0, 2}, {0, 511}, {0, 16383}, {-5, 9},
      {maximum - 3, maximum}, {std::numeric_limits<int>::min(), std::numeric_limits<int>::min() + 3}}) {
    uniform_int_distribution_custom<int> distribution(bounds.first, bounds.second);
    std::mt19937 actual(598), expected(598);
    for (int i = 0; i < 10000; ++i) {
      const int value = distribution(actual);
      assert(value >= bounds.first && value <= bounds.second);
      assert(value == reference(expected, bounds.first, bounds.second));
    }
    assert(actual() == expected());
  }
  struct BoundaryEngine {
    const uint32_t values[5] = {UINT32_MAX, 2147483648u, 0u, 2147483647u, 7u};
    int index = 0;
    uint32_t operator()() { assert(index < 5); return values[index++]; }
  } engine;
  assert(default_distribution(engine) == 0);
  assert(default_distribution(engine) == maximum);
  assert(default_distribution(engine) == 7);
  assert(engine.index == 5);
}
