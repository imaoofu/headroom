# NVIDIA GPU voltage quantisation: what the public documentation establishes

**Research date:** 2026-09-18
**Question:** What physically produces the approximately 6.25 mV grid in HWiNFO's
`GPU Core Voltage` readings on NVIDIA Turing, Ampere, and Blackwell consumer GPUs?

## Result

The public evidence does **not** support calling the grid the voltage sensor's
resolution. It also does not establish a universal 6.25 mV NVIDIA PWMVID step.

NVIDIA's public OpenVReg PWMVID specification defines the step as
`(Vmax - Vmin) / Nmax`; it does not assign one fixed voltage increment. Public
controller documentation shows that implementations differ:

| Device or interface | Documented granularity | What the number applies to |
|---|---:|---|
| NVIDIA OpenVReg Console PWMVID | No fixed value | `Vstep = (Vmax - Vmin) / Nmax`; the voltage range and number of PWM steps determine it |
| MPS MP2884A | **6.25 mV/LSB** | Reference DAC and target/command registers, including `VOUT_COMMAND` and `VOUT_OFFSET` |
| MPS MP2884A | **1 mV/LSB** | `READ_VOUT`, explicitly described as sensed output voltage |
| uPI uP9512R | PWM duty converted to an analog reference; no 6.25 mV step specified | PWMVID input and reference generation |
| uPI uP9512R | **10 mV/step** | SMBus offsets and the controller's `VOUT` report |
| Infineon XDPE132G5C | **5 or 10 mV**, user-configurable | NVIDIA PWMVID interface |

The MP2884A is the clearest warning against the original wording. One physical
controller has a 6.25 mV target-voltage DAC and a separately documented sensed
voltage report at 1 mV/LSB. A 6.25 mV telemetry grid can therefore match the
controller's command path without being the resolution of its voltage sensor.
This does not prove that any card in this project contains an MP2884A, or that
HWiNFO reads that controller's target register.

## Defensible sentence

> Across the tested cards, HWiNFO's NVIDIA `GPU Core Voltage` value is quantised
> on an approximately 6.25 mV grid; public documentation does not establish
> whether that value is a voltage request, controller target, or sensed rail
> voltage, so the grid is reported here as the granularity of the NVIDIA-reported
> voltage value, not as sensor resolution.

A stronger interpretation can be labelled as an inference:

> The 6.25 mV grid and the absence of any response to a measured 71 W change in
> board power are consistent with a requested or target-voltage value rather than
> direct rail-voltage telemetry, but the public NVIDIA and HWiNFO documentation
> does not identify the field's physical source.

The load comparison is project evidence, not vendor documentation. Board power is
also not a direct measurement of GPU-core rail current. It supports the
interpretation but does not close the documentation gap.

## 1. NVIDIA PWMVID does not have one documented universal step

NVIDIA's **Open Voltage Regulator Specification, Console, Revision 1.0**, dated
2013-01-23, describes PWMVID as a single-wire, duty-cycle-controlled voltage
interface. Section 3 states that the step depends on the selected voltage range and
number of available steps. Table 3.1 gives:

```text
Vstep = (Vmax - Vmin) / Nmax
Vout  = Vmin + N * Vstep
```

The same section says the unit pulse width is programmable. The document therefore
does not support the statement "NVIDIA PWMVID uses 6.25 mV steps." It is an older
interface specification, so it also cannot by itself prove the exact encoding used
inside a TU106, GA106, GA104, or GB206 implementation.

Source: [NVIDIA OpenVReg product page](https://www.nvidia.com/en-us/drivers/openvreg/)
and [OpenVReg Console Specification, Revision 1.0](https://international.download.nvidia.com/openvreg/openvreg-console-specification.pdf),
especially sections 3 and 3.1, pages 9-11.

Controller implementations confirm that the step is not universal. The preliminary
**Infineon XDPE132G5C Digital Multi-phase Controller datasheet**, Revision 1.31,
2018-11-14, says in section 13.1 that its NVIDIA PWMVID interface LSB is
user-configurable to **5 mV or 10 mV**. This public, distributor-hosted copy is
marked preliminary and carries confidentiality text, so it is evidence about this
part rather than a current general NVIDIA specification.

Source: [Infineon XDPE132G5C datasheet, Revision 1.31](https://www1.futureelectronics.com/doc/Infineon/XDPE132G5CG000XUMA1.pdf),
section 13.1, page 72 of the PDF.

## 2. What the controller datasheets say

### Monolithic Power Systems MP2884A

The current public **MP2884A Rev. 1.02** datasheet, dated 2025-11-14, describes an
OpenVReg-compatible PWMVID controller for graphics-card core power. It distinguishes
command and measurement paths:

- The electrical-characteristics table specifies a **10-bit ADC** and a
  **6.25 mV reference-DAC LSB**.
- `VOUT_MIN`, `VOUT_COMMAND`, `VOUT_OFFSET`, `VOUT_MAX`, and the voltage-margin
  registers use **6.25 mV/LSB**.
- `READ_VOUT` register `8Bh` is described as recording the **sensed output voltage**
  and uses **1 mV/LSB**.

Source: [MPS MP2884A datasheet, Revision 1.02](https://www.monolithicpower.com/en/documentview/productdocument/index/version/2/document_type/Datasheet/lang/en/sku/MP2884AGU/),
pages 7, 14, 29, 39-41, and 68 of the PDF.

This establishes that 6.25 mV can be a target-DAC or command-register quantum on a
GPU voltage controller. No opened source tied an MP2884A to any of the four exact
boards tested in Headroom.

### uPI uP9512R and uP9512P

The **uP9512R-DS-F0000**, November 2018, says the controller supports NVIDIA
OpenVReg Type 4i+ PWMVID. The PWMVID input is buffered and filtered to produce the
reference voltage. Its PWMVID section gives an analog duty-cycle relationship; it
does not specify a 6.25 mV digital code.

The same datasheet documents **10 mV/step** for the `VOFS0` through `VOFS4` offset
fields and for the SMBus `VOUT` register `0x2D`, which reports controller output
voltage through its ADC. This is incompatible with identifying a 6.25 mV HWiNFO
grid as the uP9512R's direct `VOUT` telemetry.

Sources:

- [uPI uP9512P manufacturer page](https://www.upi-semi.com/upisemi/products/ic/dc-dc-controller/multiple-phase-buck-controller/up9512p/)
- [uPI uP9512R-DS-F0000 public mirror](https://uploadcdn.oneyac.com/upload/document/1754981236304_9415.pdf),
  especially pages 8, 15, and 16. The full register-map PDF was found on a public
  distributor mirror, not on the current uPI product page.

Published PCB identifications show that the controller depends on the board, not
just the GPU die:

| Board that was publicly identified | GPU die | Reported core controller | Relevance |
|---|---|---|---|
| NVIDIA RTX 2070 Founders Edition | TU106 | uP9512P | Same die family as the project's MSI RTX 2060 Super, but a different board |
| NVIDIA RTX 3070 Founders Edition | GA104 | uP9512R | Same die family as the project's Gigabyte RTX 3070 Ti, but a different board |
| Zotac RTX 3060 AMP White | GA106 | uP9512R | Same die family as the project's ASUS Phoenix RTX 3060, but a different board |

Sources: [RTX 2070 FE PCB analysis](https://procompsoft.ru/obzory/nvidia-geforce-rtx-2070-founders-edition.html),
[RTX 3070 FE PCB analysis](https://www.igorslab.de/en/nvidia-geforce-rtx-3070-founders-edition-in-test-ampere-can-also-economic-and-cuddly-small/2/),
and [Zotac RTX 3060 AMP White PCB analysis](https://procompsoft.ru/obzory/zotac-gaming-geforce-rtx-3060-amp-white-edition.html).
These secondary board analyses were used only for component identification.

The project's exact boards are the MSI Ventus 2X RTX 2060 Super, ASUS Phoenix RTX
3060 12 GB, Gigabyte RTX 3070 Ti GAMING OC rev. 2.0, and Zotac RTX 5060 Ti Twin
Edge OC 16 GB. I did not find an open PCB analysis, schematic, or legible component
photograph that verified the GPU-core controller on any of those exact board
revisions. Paid or gated boardview listings were visible for some boards, but their
contents were not accessible and were not treated as evidence.

## 3. HWiNFO's source is not publicly documented closely enough

I did not find a HWiNFO document that names the exact NVIDIA API function or says
whether `GPU Core Voltage` is requested VID, a controller target, or sensed VOUT.
HWiNFO is closed source.

A 2024 HWiNFO forum thread provides useful, limited evidence. A user asked for
direct access to uP9512R register `0x2D`, stating that its reading differed from
the NVIDIA API. HWiNFO author Martin Malik replied that PWM controllers and VRs
are usually not exposed through NVAPI I2C. The user later reported that the direct
controller VOUT value rose with load and responded to a feedback modification.
This separates NVIDIA API voltage from direct uP9512R VOUT in that user's test,
but it does not document HWiNFO's internal call.

Source: [HWiNFO forum, "Nvidia I2C NVVDD core voltage (feedback sense)"](https://www.hwinfo.com/forum/threads/nvidia-i2c-nvvdd-core-voltage-feedback-sense.9600/),
posts 1-4, 2024-03-29 to 2024-04-16.

HWiNFO does document display rounding. In a separate thread, its author said values
shown with three decimal places are rounded and advised selecting four decimals for
accuracy. Thus an exact 6.25 mV source grid can appear as alternating 6 mV and 7 mV
jumps in a three-decimal display. That display rounding does not explain why the
underlying readings occupy a 6.25 mV grid. Raw CSV values or a four-decimal display
should be used to establish the grid.

Source: [HWiNFO forum, "Min value is not displayed properly"](https://www.hwinfo.com/forum/threads/nitpick-min-value-is-not-displayed-properly.2451/),
post 2, 2016-05-12.

There is independent open-source evidence for an NVIDIA API voltage path. The
current LibreHardwareMonitor NVIDIA backend creates `GPU Core Voltage` from
`GetVoltRailsStatus`, combines two fields named `CoreMicrovolts` and
`CoreMicrovoltsHigh`, and divides by 1,000,000. That code adds no 6.25 mV
quantisation. It is evidence about LibreHardwareMonitor, not proof that HWiNFO uses
the same private call. A microvolt storage unit is also not evidence of one-microvolt
physical resolution.

Source: [LibreHardwareMonitor `NvidiaGpu.cs`](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/blob/master/LibreHardwareMonitorLib/Hardware/Gpu/NvidiaGpu.cs),
the voltage-sensor creation near lines 2809-2819 and update near lines 3439-3450.
Reverse-engineered wrappers identify the private call as
`ClientVoltRailsGetStatus`, interface ID `0x465F9BCF`, but NVIDIA's public NVAPI
headers do not document its physical semantics. See [LACT issue 936](https://github.com/ilya-zlobintsev/LACT/issues/936)
and [Loong's NVAPI voltage gist](https://gist.github.com/Loong0x00/0163c73d9379d6e683d83c2718791048).

## 4. Reverse engineering and VBIOS documentation

NVIDIA's public **BIOS Information Table Specification** names pointers to the
Voltage Frequency, Voltage Rail, Voltage Device, and Voltage Policy tables. It does
not publish those tables' formats or voltage units.

Source: [NVIDIA BIOS Information Table Specification](https://nvidia.github.io/open-gpu-doc/BIOS-Information-Table/BIOS-Information-Table.html),
BIT token `P`, especially the table-pointer list.

The envytools `nvbios` parser contains support for older voltage-table formats. For
one legacy table version it reads a table-specific `step_uv` value and prints it in
microvolts; it treats PWM-mode tables differently. This is evidence that legacy
VBIOS voltage steps were table-specific, not evidence for a 6.25 mV step on Turing,
Ampere, or Blackwell.

Source: [envytools `nvbios.c`, commit f102b82381f3f11cee113d16374c87091db039d9](https://github.com/envytools/envytools/blob/f102b82381f3f11cee113d16374c87091db039d9/nvbios/nvbios.c),
voltage-table parsing around lines 1774-1916.

I searched the NVIDIA open GPU kernel modules, Nouveau/envytools material, and
public PMU/GSP-related code for a modern GeForce voltage-rail structure or a
documented Turing-through-Blackwell step. I did not find one. In the public NVIDIA
open modules, `ctrl2080volt.h` contains no usable voltage-control definitions.

Source: [NVIDIA open GPU kernel modules `ctrl2080volt.h`](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/main/src/common/sdk/nvidia/inc/ctrl/ctrl2080/ctrl2080volt.h).

## What remains unresolved

- The physical source and semantics of HWiNFO's NVIDIA `GPU Core Voltage` field.
- The encoding used by NVIDIA's private voltage-rail status API on TU106, GA106,
  GA104, and GB206.
- The modern VBIOS Voltage Frequency, Voltage Rail, Voltage Device, and Voltage
  Policy table formats and units.
- The GPU-core voltage-controller part numbers on the four exact tested board
  revisions. In particular, no verified public GB206/Zotac Twin Edge controller
  identification was found.
- Whether the approximately 6.25 mV grid originates in a GPU-side VID table, a
  controller target DAC, firmware conversion, the private API's returned field, or
  another layer. The public evidence narrows the interpretation but does not select
  one of these mechanisms.

Some boardview and schematic sites were paywalled or required accounts. TechPowerUp
PCB pages were blocked by automated-access controls during this search. The full
uP9512R register-map datasheet was reachable only through a public distributor
mirror. No unavailable datasheet was replaced with specifications from a related
part.

## Search record and framing boundary

The external documentation search was performed before consulting Headroom files
for the exact board model names. The assistant had read the repository's authority
document during an earlier task, so this was not a pristine cold-reader novelty
check. Repository framing was used only after the main source comparison to map the
result to the four board SKUs.

Exact board follow-up queries included:

```text
"MSI Ventus 2X RTX 2060 Super" PWM controller uP9512 PCB
"ASUS Phoenix RTX 3060" PWM controller PCB uP9512
"Gigabyte RTX 3070 Ti GAMING OC rev 2.0" PWM controller PCB
"Zotac RTX 5060 Ti Twin Edge OC" PWM controller PCB
"MSI RTX 2060 SUPER VENTUS" uP9512R
"PH-RTX3060-12G" uP9512R OR "uP9512"
"GV-N307TGAMING OC-8GD" PWM controller
"ZT-B50620H-10M" PCB controller
```

The complete query transcript for the earlier interface, datasheet, HWiNFO, and
reverse-engineering searches was not retained in a form that can be copied exactly,
so it is not reconstructed here as an exact log. Every cited page or document above
was opened during this pass unless its access limitation is stated explicitly.
