#include "program.h"
#include <cassert>
#include <cmath>

// Evolution reuses an output slot across generations. Sanitizers must find no
// leaks or use-after-free when hoist mutation repeatedly replaces its nodes.
int main() {
  genetic::param params;
  params.num_features = 3;
  params.init_depth[0] = 2;
  params.init_depth[1] = 3;
  params.function_set = {genetic::node::type::add, genetic::node::type::mul};
  PhiloxEngine rng(598);
  genetic::program parent, output;
  genetic::build_program(parent, params, rng);
  genetic::build_program(output, params, rng);
  const float data[] = {1.0f, -1.0f, 2.0f, -2.0f, 0.5f, -0.5f};
  for (int i = 0; i < 1000; ++i) {
    genetic::hoist_mutation(parent, output, params, rng);
    genetic::program_t ptr = &output;
    float predictions[2];
    genetic::execute(ptr, 2, 1, data, predictions);
    assert(std::isfinite(predictions[0]) && std::isfinite(predictions[1]));
  }
}
