"""
DSParser Benchmark Tool

This script benchmarks the DSParser tool under various configurations
to provide objective performance metrics.
"""

import os
import sys
import time
import argparse
import subprocess
import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm
import multiprocessing
import psutil

def format_size(size_bytes):
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def get_file_info(file_path):
    """Get file size and line count"""
    size = os.path.getsize(file_path)
    with open(file_path, 'rb') as f:
        line_count = sum(1 for _ in f)
    return size, line_count

def run_benchmark(input_file, output_dir, chunk_sizes, worker_counts):
    """Run benchmark with various configurations"""
    results = []
    file_size, line_count = get_file_info(input_file)
    
    print(f"File: {input_file}")
    print(f"Size: {format_size(file_size)}")
    print(f"Lines: {line_count:,}")
    print("\nStarting performance tests...")
    
    total_runs = len(chunk_sizes) * len(worker_counts)
    run_count = 0
    
    for chunk_size in chunk_sizes:
        for workers in worker_counts:
            run_count += 1
            print(f"\nTest {run_count}/{total_runs}: chunk_size={chunk_size}MB, workers={workers}")
            
            # Clear memory cache before each test (Linux only)
            if sys.platform.startswith('linux'):
                os.system('sync; echo 3 > /proc/sys/vm/drop_caches')
            
            # Run command and measure time
            output_path = os.path.join(output_dir, f"benchmark_c{chunk_size}_w{workers}")
            os.makedirs(output_path, exist_ok=True)
            
            # Calculate minimum iterations to ensure test runs for at least 2 seconds
            # For small files, we'll run multiple iterations to get more accurate measurements
            min_iterations = 1
            if file_size < 50 * 1024 * 1024:  # if file is smaller than 50MB
                min_iterations = max(5, int(50 * 1024 * 1024 / file_size))
                print(f"Small file detected. Running {min_iterations} iterations for accurate measurement")
            
            # Initialize measurement variables
            total_elapsed_time = 0
            total_memory_used = 0
            successful_runs = 0
            
            for i in range(min_iterations):
                print(f"  Iteration {i+1}/{min_iterations}")
                
                # Monitor memory before
                start_memory = psutil.virtual_memory().used
                start_time = time.perf_counter()  # More precise time measurement
                
                cmd = [
                    sys.executable, "-m", "dsparser",
                    "--input", input_file,
                    "--output", output_path,
                    "--chunk-size", str(chunk_size),
                    "--workers", str(workers)
                ]
                
                process = subprocess.Popen(
                    cmd, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                
                stdout, stderr = process.communicate()
                
                end_time = time.perf_counter()
                end_memory = psutil.virtual_memory().used
                
                # Check if process completed successfully
                if process.returncode != 0:
                    print(f"  Error executing command: {stderr}")
                    continue
                
                # Calculate measurements
                elapsed_time = end_time - start_time
                memory_used = end_memory - start_memory
                
                # Print iteration results
                print(f"  Time: {elapsed_time:.2f} sec")
                print(f"  Memory: {format_size(memory_used)}")
                
                # Accumulate measurements
                total_elapsed_time += elapsed_time
                total_memory_used += memory_used
                successful_runs += 1
            
            # Skip this configuration if all runs failed
            if successful_runs == 0:
                print("  All iterations failed for this configuration. Skipping.")
                continue
            
            # Calculate average metrics
            avg_elapsed_time = total_elapsed_time / successful_runs
            avg_memory_used = total_memory_used / successful_runs
            
            throughput = file_size / avg_elapsed_time
            lines_per_sec = line_count / avg_elapsed_time
            
            results.append({
                'chunk_size': chunk_size,
                'workers': workers,
                'time': avg_elapsed_time,
                'memory': avg_memory_used,
                'throughput': throughput,
                'lines_per_sec': lines_per_sec
            })
            
            print(f"Average results after {successful_runs} iterations:")
            print(f"Time: {avg_elapsed_time:.2f} sec")
            print(f"Memory: {format_size(avg_memory_used)}")
            print(f"Speed: {format_size(throughput)}/sec")
            print(f"Lines/sec: {lines_per_sec:.2f}")
    
    return results

def plot_results(results, output_dir):
    """Create plots from benchmark results"""
    if not results:
        print("No valid benchmark results to plot.")
        return
        
    plt.figure(figsize=(15, 10))
    
    # Group results by workers
    worker_groups = {}
    for r in results:
        if r['workers'] not in worker_groups:
            worker_groups[r['workers']] = []
        worker_groups[r['workers']].append(r)
    
    # Plot 1: Time by chunk size and workers
    plt.subplot(2, 2, 1)
    for workers, group in worker_groups.items():
        chunk_sizes = [r['chunk_size'] for r in group]
        times = [r['time'] for r in group]
        plt.plot(chunk_sizes, times, 'o-', label=f"{workers} workers")
    
    plt.title('Processing Time')
    plt.xlabel('Chunk Size (MB)')
    plt.ylabel('Time (sec)')
    plt.grid(True)
    plt.legend()
    
    # Plot 2: Throughput
    plt.subplot(2, 2, 2)
    for workers, group in worker_groups.items():
        chunk_sizes = [r['chunk_size'] for r in group]
        throughputs = [r['throughput'] / 1024 / 1024 for r in group]  # MB/s
        plt.plot(chunk_sizes, throughputs, 'o-', label=f"{workers} workers")
    
    plt.title('Processing Speed')
    plt.xlabel('Chunk Size (MB)')
    plt.ylabel('Speed (MB/sec)')
    plt.grid(True)
    plt.legend()
    
    # Plot 3: Memory usage
    plt.subplot(2, 2, 3)
    for workers, group in worker_groups.items():
        chunk_sizes = [r['chunk_size'] for r in group]
        memory = [r['memory'] / 1024 / 1024 for r in group]  # MB
        plt.plot(chunk_sizes, memory, 'o-', label=f"{workers} workers")
    
    plt.title('Memory Usage')
    plt.xlabel('Chunk Size (MB)')
    plt.ylabel('Memory (MB)')
    plt.grid(True)
    plt.legend()
    
    # Plot 4: Lines per second
    plt.subplot(2, 2, 4)
    for workers, group in worker_groups.items():
        chunk_sizes = [r['chunk_size'] for r in group]
        lines = [r['lines_per_sec'] for r in group]
        plt.plot(chunk_sizes, lines, 'o-', label=f"{workers} workers")
    
    plt.title('Processing Rate')
    plt.xlabel('Chunk Size (MB)')
    plt.ylabel('Lines/sec')
    plt.grid(True)
    plt.legend()
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'benchmark_results.png'), dpi=300)
    plt.savefig(os.path.join(output_dir, 'benchmark_results.pdf'))
    
    # Create summary table for README
    if results:
        best_result = max(results, key=lambda x: x['throughput'])
        with open(os.path.join(output_dir, 'benchmark_summary.md'), 'w', encoding='utf-8') as f:
            f.write("# DSParser Benchmark Results\n\n")
            f.write(f"File: {best_result['chunk_size']} MB, {best_result['workers']} workers\n\n")
            f.write("| Metric | Value |\n")
            f.write("|---------|----------|\n")
            f.write(f"| Processing Speed | {format_size(best_result['throughput'])}/sec |\n")
            f.write(f"| Messages per second | {best_result['lines_per_sec']:.2f} |\n")
            f.write(f"| Processing time | {best_result['time']:.2f} sec |\n")
            f.write(f"| Memory usage | {format_size(best_result['memory'])} |\n\n")
            
            f.write("## Complete Results\n\n")
            f.write("| Chunk Size (MB) | Workers | Time (sec) | Memory | MB/sec | Lines/sec |\n")
            f.write("|-----------------|---------|------------|--------|--------|-----------|\n")
            
            for r in sorted(results, key=lambda x: (x['chunk_size'], x['workers'])):
                f.write(f"|        {r['chunk_size']}        |    {r['workers']}    |    {r['time']:.2f}    |{format_size(r['memory'])} |  {r['throughput']/1024/1024:.2f}  |  {r['lines_per_sec']:.2f} |\n")

def main():
    parser = argparse.ArgumentParser(description='DSParser Benchmark Tool')
    parser.add_argument('--input', '-i', required=True, help='Input HTML file to parse')
    parser.add_argument('--output', '-o', default='benchmark_results', help='Output directory for benchmark results')
    parser.add_argument('--chunk-sizes', '-c', type=int, nargs='+', default=[5, 10, 20, 50], help='Chunk sizes to test (MB)')
    parser.add_argument('--workers', '-w', type=int, nargs='+', help='Worker counts to test')
    parser.add_argument('--quick', '-q', action='store_true', help='Run a quick benchmark with fewer configurations')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: File {args.input} not found")
        return 1
    
    # Set default worker counts based on CPU or quick mode
    if args.workers is None:
        if args.quick:
            args.workers = [1, multiprocessing.cpu_count()]
        else:
            cpu_count = multiprocessing.cpu_count()
            args.workers = [1, max(1, cpu_count//4), max(1, cpu_count//2), cpu_count]
    
    # Use fewer chunk sizes in quick mode
    if args.quick and not args.chunk_sizes:
        args.chunk_sizes = [10, 50]
    
    os.makedirs(args.output, exist_ok=True)
    
    results = run_benchmark(args.input, args.output, args.chunk_sizes, args.workers)
    plot_results(results, args.output)
    
    print("\nBenchmark completed! Results saved to:", args.output)
    return 0

if __name__ == "__main__":
    sys.exit(main())