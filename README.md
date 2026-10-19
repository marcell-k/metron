# Metron

Terminal statistics tool. Descriptive stats, distributions, correlation, ASCII plots.

## Install

```bash
uv sync
uv run metron --help
```

## Commands

| Command        | Description                                   |
| -------------- | --------------------------------------------- |
| `descriptive`  | Count, mean, median, mode, std, MAD, quartiles, skewness, kurtosis |
| `histogram`    | ASCII histogram, configurable bins            |
| `frequency`    | Frequency table                               |
| `ecdf`         | Empirical cumulative distribution plot        |
| `zscore`       | Z-score distribution, flags `abs(z) > 3`      |
| `outlier`      | Outliers via `mad` (default) or `iqr`         |
| `relationship` | Covariance, Pearson, Spearman, R², regression |

## Input

Numbers separated by comma (default) or newline. Read from file or stdin:

```bash
metron descriptive data/x.txt
echo "1,2,33,45,5,1,23,5,2" | metron zscore
fd . --type file --exec wc -l | awk '{print $1}' | metron descriptive
```

Custom separator: `--sep ";"`.

## Usage

### Descriptive statistics

```bash
metron descriptive data/x.txt
```

```text
Descriptive statistics:
------------------------
Count:            100000
Sum:               315.0
Minimum:           -8.64
Maximum:            8.14
Range:              16.8
Mean:            0.00315
Median:            -0.01
Mode:              -0.39
Mode count:          243

Spread and shape:
------------------------
Variance:           4.01
Std:                 2.0
MAD:                1.36
Q1:                -1.35
Q3:                 1.36
IQR:                2.71
Tukey's lower:     -5.41
Tukey's upper:      5.42
Skewness:          0.002
Excess-kurt:      -0.006
```

### Histogram

```bash
metron histogram data/x.txt --bins 10
```

```text
    │             █  █
    │             █  █
    │             █  █  █
    │          █  █  █  █
    │ █  █  █  █  █  █  █  █  █  █
    └──────────────────────────────
      0  1  2  3  4  5  6  7  8  9
Range: (-8.64, 8.14)   Bin width: 1.678
```

Horizontal:

```bash
metron histogram data/x.txt --horizontal
```

```text
[-8.64, -6.96) │█ 28
[-6.96, -5.28) │█ 393
[-5.28, -3.61) │██ 3160
[-3.61, -1.93) │█████████ 13172
[-1.93, -0.25) │██████████████████ 28274
 [-0.25, 1.43) │████████████████████ 30959
  [1.43, 3.11) │████████████ 17977
  [3.11, 4.78) │███ 5203
  [4.78, 6.46) │█ 766
  [6.46, 8.14] │█ 68
               └────────────────────────
Range: (-8.64, 8.14)   Bin width: 1.678
```

### Outlier detection

```bash
metron outlier data/x.txt --method iqr
```

```text
               Outlier detection, using: iqr
  8.14│          .           .             .             .
      │  .. . . . ..... . ....... . .  .   .. .. . . . ... ......
 6.043│ ......  ...................................................
      │............................................................
 3.945│............................................................
      │.::::::::::::::::::::::::::::::::::::::::::::::::::::::::::.
 1.848│:**********************************************************:
      │:##########################################################:
 -0.25│:##########################################################:
      │:*####***#**#**##*##****#*#*#***##*****#*###*#***#**#*#*#*#:
-2.348│:::::::::::::**::::*:::::*:::*::::::::*:::::::::::::::*::::.
      │......................:............:...:..::................
-4.445│............................................................
      │............................................................
-6.543│............... ...   ....... ...  .....................  .
      │.  ..    ..    . . . .. ..    .. .          ...         .
 -8.64│ .                           .                       .
      └────────────────────────────────────────────────────────────
       1                                                     100000

Median: -0.01   Fences: (-5.415, 5.425)
Outliers (655): [-8.64, -8.51, -8.21, 8.14, -8.03, 7.9, -7.87, -7.84, 7.78, 7.73], ... +645 more
```

### Relationship

```bash
metron relationship data/x.txt data/y.txt
```

```text
               Scatter with least-squares fit
  8.36│                                                          .
      │                                              ........ ...
 6.304│                                      .. . .................
      │                                    . .....................
 4.247│                               ..........................
      │                            .............:............ . .
 2.191│                      ...........:::**::::...........
      │                   . .......:::**####*::..........
 0.135│                 ........::*######**::.........
      │           .  ........::**####**::...........
-1.921│           .........:::****:::.........
      │       . ...........::::............
-3.977│      .........................
      │  . ...................... .
-6.034│  ·....................
      │.·. .... ...... .
 -8.09│   .
      └────────────────────────────────────────────────────────────
       -8.64                                                   8.14

Relationship analysis:
------------------------
Covariance:          3.2
Pearson:           0.848 (0.846-0.85), 95% confidence
Spearman:          0.837 (0.835-0.839), 95% confidence
R²:                0.719
Slope:               0.8
Intercept:       0.00371
```
