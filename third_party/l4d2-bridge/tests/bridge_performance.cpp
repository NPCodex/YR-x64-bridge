#define WIN32_LEAN_AND_MEAN
#include "bridge_performance.h"
#include <stdexcept>
int main() {
  { yr_perf::Scope sample(yr_perf::Upload, 123); }
  if(yr_perf::calls[yr_perf::Upload].load()!=0){throw std::runtime_error("disabled counters changed");}
  yr_perf::enabled.store(true);
  { yr_perf::Scope sample(yr_perf::Upload); sample.addBytes(123); }
  { yr_perf::Scope sample(yr_perf::FullWait, 0, false); }
  if(yr_perf::calls[yr_perf::FullWait].load()!=0){throw std::runtime_error("inactive wait counted");}
  { yr_perf::Scope sample(yr_perf::FullWait, 0, false); sample.begin(); Sleep(2); }
  yr_perf::flush();
  if(yr_perf::calls[yr_perf::Upload].load()!=1 || yr_perf::bytes[yr_perf::Upload].load()!=123 || yr_perf::calls[yr_perf::FullWait].load()!=1){throw std::runtime_error("enabled counters mismatch");}
}
