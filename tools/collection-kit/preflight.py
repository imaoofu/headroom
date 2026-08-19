"""
Prove this GPU can actually run the benchmark, before any clock is locked.

WHY torch.cuda.is_available() IS NOT ENOUGH
    It reports whether a CUDA device and driver were found. It does NOT report whether this
    PyTorch build contains compiled kernels for that device's compute capability. A wheel
    built without, say, sm_86 will happily say True on an Ampere card and then fail on the
    first real operation with "no kernel image is available for execution on the device".

    That failure would land mid-sweep, on someone else's machine, with the GPU clock-locked
    and nobody available to debug it. So this runs the two operations the workloads actually
    use - a matmul and an elementwise add - and synchronises to force any deferred launch
    error to surface here instead.

Prints one line per fact. Exits non-zero with a readable reason on any failure.
"""

import sys


def main():
    try:
        import torch
    except Exception as error:
        print(f"FAIL|torch did not import: {error}")
        return 2

    if not torch.cuda.is_available():
        print("FAIL|PyTorch loaded but reports no CUDA device. Driver problem, or no NVIDIA GPU.")
        return 3

    name = torch.cuda.get_device_name(0)
    capability = torch.cuda.get_device_capability(0)
    smVersion = f"sm_{capability[0]}{capability[1]}"
    archList = list(torch.cuda.get_arch_list())

    print(f"INFO|device={name}")
    print(f"INFO|capability={smVersion}")
    print(f"INFO|built_for={','.join(archList)}")

    # A build lists the architectures it was compiled for. Ampere sm_86 code also runs on
    # sm_86; newer cards can fall back to PTX JIT if the build ships PTX, which is why this
    # is a warning rather than a refusal - the kernel test below is the real verdict.
    if archList and not any(smVersion.replace("sm_", "") in a for a in archList):
        print(f"WARN|{smVersion} is not in the build's architecture list")

    try:
        device = torch.device("cuda:0")
        left = torch.randn((512, 512), device=device, dtype=torch.float32)
        right = torch.randn((512, 512), device=device, dtype=torch.float32)
        product = torch.matmul(left, right)

        source = torch.randn(1 << 20, device=device, dtype=torch.float32)
        other = torch.randn(1 << 20, device=device, dtype=torch.float32)
        destination = torch.empty(1 << 20, device=device, dtype=torch.float32)
        torch.add(source, other, alpha=2.0, out=destination)

        # CUDA launches are asynchronous; without this the errors surface later, elsewhere.
        torch.cuda.synchronize()

        if not torch.isfinite(product).all() or not torch.isfinite(destination).all():
            print("FAIL|kernels ran but produced non-finite values. Unstable GPU or bad memory.")
            return 5
    except Exception as error:
        message = str(error).replace("\n", " ")[:300]
        print(f"FAIL|the GPU could not run the benchmark kernels: {message}")
        return 4
    finally:
        try:
            torch.cuda.empty_cache()
        except Exception:
            pass

    freeBytes, totalBytes = torch.cuda.mem_get_info(0)
    print(f"INFO|vram_total_gb={totalBytes / 1e9:.1f}")
    print(f"INFO|vram_free_gb={freeBytes / 1e9:.1f}")

    # membw allocates three buffers of 256M float32 = 3.07 GB, gemm about 0.8 GB. Below this
    # the workload will OOM partway through a clock-locked sweep.
    requiredBytes = 4.0e9
    if freeBytes < requiredBytes:
        print(f"FAIL|only {freeBytes / 1e9:.1f} GB of VRAM free; the benchmark needs about "
              f"{requiredBytes / 1e9:.1f} GB. Close anything using the GPU.")
        return 6

    print("OK|this GPU can run the benchmark")
    return 0


if __name__ == "__main__":
    sys.exit(main())
