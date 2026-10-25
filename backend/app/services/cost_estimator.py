from typing import Dict, Any
from ..schemas.schemas import CostEstimateRequest, CostEstimateResponse, CostBreakdown

class CostEstimator:
    @staticmethod
    def estimate_costs(req: CostEstimateRequest) -> CostEstimateResponse:
        """
        Calculates traceable infrastructure cost estimates comparing Greedy and Beam Search
        across Local CPU, Cloud CPU, and Cloud GPU environments.
        """
        n = req.workload_sentences
        r_greedy = max(req.sentences_per_second_greedy, 0.001)
        r_beam = max(req.sentences_per_second_beam, 0.001)
        
        # 1. Inference Durations (seconds)
        time_sec_greedy = n / r_greedy
        time_sec_beam = n / r_beam
        
        # 2. Local CPU Costs (based on electricity consumption)
        # Power (kW) = Watts / 1000
        # Energy (kWh) = Power * (time_sec / 3600)
        # Cost = Energy * $/kWh
        power_kw = req.local_power_watts / 1000.0
        kwh_cost = req.local_kwh_cost
        
        local_cost_greedy = power_kw * (time_sec_greedy / 3600.0) * kwh_cost
        local_cost_beam = power_kw * (time_sec_beam / 3600.0) * kwh_cost
        
        # Cost per 1000 sentences
        local_1k_greedy = power_kw * ((1000.0 / r_greedy) / 3600.0) * kwh_cost
        local_1k_beam = power_kw * ((1000.0 / r_beam) / 3600.0) * kwh_cost
        
        # 3. Cloud CPU Costs
        p_cloud_cpu = req.cloud_cpu_hourly_cost
        cloud_cpu_cost_greedy = (time_sec_greedy / 3600.0) * p_cloud_cpu
        cloud_cpu_cost_beam = (time_sec_beam / 3600.0) * p_cloud_cpu
        cloud_cpu_1k_greedy = ((1000.0 / r_greedy) / 3600.0) * p_cloud_cpu
        cloud_cpu_1k_beam = ((1000.0 / r_beam) / 3600.0) * p_cloud_cpu
        
        # 4. Cloud GPU Costs (assuming GPU throughput is typically 3.5x - 5x CPU throughput)
        # Here we use entered hourly price and proportional compute time
        p_cloud_gpu = req.cloud_gpu_hourly_cost
        # Projected GPU speedup factor ~3.5x for seq2seq batching
        gpu_speedup = 3.5
        time_sec_gpu_greedy = time_sec_greedy / gpu_speedup
        time_sec_gpu_beam = time_sec_beam / gpu_speedup
        cloud_gpu_cost_greedy = (time_sec_gpu_greedy / 3600.0) * p_cloud_gpu
        cloud_gpu_cost_beam = (time_sec_gpu_beam / 3600.0) * p_cloud_gpu
        cloud_gpu_1k_greedy = ((1000.0 / (r_greedy * gpu_speedup)) / 3600.0) * p_cloud_gpu
        cloud_gpu_1k_beam = ((1000.0 / (r_beam * gpu_speedup)) / 3600.0) * p_cloud_gpu
        
        # Monthly continuous uptime (730 hours / month)
        monthly_hours = 730.0
        
        return CostEstimateResponse(
            workload_sentences=n,
            local_cpu_greedy=CostBreakdown(
                inference_seconds=round(time_sec_greedy, 2),
                cost_per_1000_sentences=round(local_1k_greedy, 6),
                total_workload_cost=round(local_cost_greedy, 6),
                monthly_continuous_cost=round(power_kw * monthly_hours * kwh_cost, 2)
            ),
            local_cpu_beam=CostBreakdown(
                inference_seconds=round(time_sec_beam, 2),
                cost_per_1000_sentences=round(local_1k_beam, 6),
                total_workload_cost=round(local_cost_beam, 6),
                monthly_continuous_cost=round(power_kw * monthly_hours * kwh_cost, 2)
            ),
            cloud_cpu_greedy=CostBreakdown(
                inference_seconds=round(time_sec_greedy, 2),
                cost_per_1000_sentences=round(cloud_cpu_1k_greedy, 6),
                total_workload_cost=round(cloud_cpu_cost_greedy, 6),
                monthly_continuous_cost=round(monthly_hours * p_cloud_cpu, 2)
            ),
            cloud_cpu_beam=CostBreakdown(
                inference_seconds=round(time_sec_beam, 2),
                cost_per_1000_sentences=round(cloud_cpu_1k_beam, 6),
                total_workload_cost=round(cloud_cpu_cost_beam, 6),
                monthly_continuous_cost=round(monthly_hours * p_cloud_cpu, 2)
            ),
            cloud_gpu_greedy=CostBreakdown(
                inference_seconds=round(time_sec_gpu_greedy, 2),
                cost_per_1000_sentences=round(cloud_gpu_1k_greedy, 6),
                total_workload_cost=round(cloud_gpu_cost_greedy, 6),
                monthly_continuous_cost=round(monthly_hours * p_cloud_gpu, 2)
            ),
            cloud_gpu_beam=CostBreakdown(
                inference_seconds=round(time_sec_gpu_beam, 2),
                cost_per_1000_sentences=round(cloud_gpu_1k_beam, 6),
                total_workload_cost=round(cloud_gpu_cost_beam, 6),
                monthly_continuous_cost=round(monthly_hours * p_cloud_gpu, 2)
            ),
            methodology_note=(
                "Estimates are derived from measured sentences/sec throughput. Local cost reflects "
                "active CPU electrical wattage. Cloud cost reflects pure billed instance compute time. "
                "GPU throughput models an empirical 3.5x batching acceleration factor."
            )
        )

cost_estimator = CostEstimator()
