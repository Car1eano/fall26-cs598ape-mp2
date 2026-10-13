#include "src/reg_stack.h"
#include <cassert>
#include <random>
#include <vector>

// An independent vector model checks ordering and the documented overflow /
// underflow behavior, including capacity one and the real evaluator capacity.
template <int Capacity> void check_stack() {
  genetic::stack<float, Capacity> stack;
  std::vector<float> reference;
  auto check = [&] {
    assert(stack.size() == static_cast<int>(reference.size()));
    assert(stack.empty() == reference.empty());
    assert(stack.full() == (reference.size() == Capacity));
  };
  assert(stack.pop() == 0.0f);
  for (int i = 0; i < Capacity; ++i) {
    stack.push(static_cast<float>(i + 1));
    reference.push_back(static_cast<float>(i + 1));
    check();
  }
  stack.push(-999.0f);
  check();
  while (!reference.empty()) {
    assert(stack.pop() == reference.back());
    reference.pop_back();
    check();
  }
  assert(stack.pop() == 0.0f);
  std::mt19937 rng(598);
  for (int i = 0; i < 100000; ++i) {
    if (rng() % 2) {
      float value = static_cast<float>(static_cast<int>(rng() % 2001) - 1000);
      stack.push(value);
      if (reference.size() < Capacity) reference.push_back(value);
    } else {
      float expected = reference.empty() ? 0.0f : reference.back();
      assert(stack.pop() == expected);
      if (!reference.empty()) reference.pop_back();
    }
    check();
  }
}

int main() {
  check_stack<1>();
  check_stack<20>();
}
