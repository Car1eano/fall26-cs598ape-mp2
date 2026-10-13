#include "program.h"
#include <cassert>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <random>
#include <vector>

using genetic::node;

// Prefix-tree recursion is independent of the production stack interpreter.
float reference(const node *nodes, int &pos, const float *data, int rows, int row) {
  const node &n = nodes[pos++];
  if (n.t == node::type::constant) return n.u.val;
  if (n.t == node::type::variable) return data[n.u.fid * rows + row];
  const float a = reference(nodes, pos, data, rows, row);
  switch (n.t) {
  case node::type::abs: return std::fabs(a);
  case node::type::sin: return std::sin(a);
  case node::type::cos: return std::cos(a);
  case node::type::log: return std::fabs(a) < 0.001f ? 0.0f : std::log(std::fabs(a));
  case node::type::sq: return a * a;
  case node::type::sqrt: return std::sqrt(std::fabs(a));
  default: break;
  }
  const float b = reference(nodes, pos, data, rows, row);
  switch (n.t) {
  case node::type::add: return a + b;
  case node::type::sub: return a - b;
  case node::type::mul: return a * b;
  case node::type::fdim: return std::fdim(a, b);
  default: assert(false); return 0.0f;
  }
}

void build(std::vector<node> &nodes, std::mt19937 &rng, int depth) {
  if (depth == 0 || rng() % 4 == 0) {
    if (rng() % 2) nodes.emplace_back(static_cast<int>(rng() % 3));
    else nodes.emplace_back((static_cast<int>(rng() % 4001) - 2000) / 1000.0f);
    return;
  }
  const node::type functions[] = {node::type::add, node::type::sub, node::type::mul,
      node::type::fdim, node::type::abs, node::type::sin, node::type::cos,
      node::type::log, node::type::sq, node::type::sqrt};
  const int choice = rng() % 10;
  nodes.emplace_back(functions[choice]);
  build(nodes, rng, depth - 1);
  if (choice < 4) build(nodes, rng, depth - 1);
}

int main() {
  constexpr int Rows = 7;
  // Include zero and values around protected-log's threshold; column major.
  const float data[] = {0.0f, -0.0f, 0.0009f, 0.001f, -0.001f, 1.0f, -2.0f,
                       1.0f, -1.0f, 2.0f, -2.0f, 0.0f, 0.5f, -0.5f,
                       -0.5f, 0.5f, 0.0f, 3.0f, -3.0f, 2.0f, 1.0f};
  std::mt19937 rng(598);
  for (int i = 0; i < 1000; ++i) {
    std::vector<node> nodes;
    build(nodes, rng, 6);
    genetic::program program;
    program.len = static_cast<int>(nodes.size());
    program.nodes = new node[nodes.size()];
    std::copy(nodes.begin(), nodes.end(), program.nodes);
    genetic::program_t ptr = &program;
    float actual[Rows];
    genetic::execute(ptr, Rows, 1, data, actual);
    for (int row = 0; row < Rows; ++row) {
      int pos = 0;
      const float expected = reference(nodes.data(), pos, data, Rows, row);
      assert(pos == program.len);
      if (std::isnan(expected)) assert(std::isnan(actual[row]));
      else assert(std::memcmp(&expected, &actual[row], sizeof(float)) == 0);
    }
  }
}
