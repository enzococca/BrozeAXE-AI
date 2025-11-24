# Morphometric Measurement System Investigation Report
## Savignano Bronze Axes - Critical Coordinate System Errors

**Date:** November 10, 2025
**Investigator:** Archaeological Classifier System Analysis
**File:** `/Users/enzo/Documents/BrozeAXE-AI/archaeological-classifier/acs/savignano/morphometric_extractor.py`

---

## Executive Summary

The morphometric measurement system for Savignano bronze axes contains **CRITICAL COORDINATE SYSTEM ERRORS** that produce completely incorrect measurements. The code documentation states one coordinate convention, but the actual PCA transformation produces the opposite mapping, causing all axis-dependent measurements to be wrong.

### Severity: CRITICAL
- Socket (incavo) width: **OFF BY 3-4X** (measures 28mm instead of 3-9mm)
- Butt (tallone) thickness: **IMPOSSIBLE** (measures 34.65mm when total axe is only 15mm thick)
- Width measurements: **LOGICALLY INCONSISTENT** (minimum wider than maximum)

---

## Part 1: Root Cause Analysis

### The Coordinate System Mismatch

**Code Documentation Says (lines 61-64):**
```
Convenzione:
- Asse Z: lunghezza ascia (tallone -> tagliente)  [LENGTH]
- Asse X: larghezza                                [WIDTH]
- Asse Y: spessore                                 [THICKNESS]
```

**Reality from PCA Transform:**
```
ACTUAL COORDINATE MAPPING:
- Axis X (PCA[:, 0]): 163.29mm → LENGTH (longest dimension)
- Axis Y (PCA[:, 1]): 56.28mm  → WIDTH (medium dimension)
- Axis Z (PCA[:, 2]): 15.19mm  → THICKNESS (shortest dimension)
```

**The Truth:**
- PCA automatically orders components by variance
- Largest variance → X axis (163mm length)
- Medium variance → Y axis (56mm width)
- Smallest variance → Z axis (15mm thickness)

**The code assumes the OPPOSITE mapping!**

---

## Part 2: Detailed Error Analysis

### Error #1: Tallone (Butt) Measurements

**Location:** Lines 151-162 in `analyze_butt()`

**Current Code:**
```python
tallone_larghezza = x_values.max() - x_values.min()  # Line 156
tallone_spessore = y_values.max() - y_values.min()   # Line 157
```

**What It Actually Measures:**
```
tallone_larghezza = 82.44mm  ← Measures X range (LENGTH direction)
tallone_spessore = 34.65mm   ← Measures Y range (WIDTH direction)
```

**What It SHOULD Measure:**
```
tallone_larghezza should be Y range = 34.65mm (actual width at butt)
tallone_spessore should be Z range = 1.52mm (actual thickness at butt)
```

**Impact:**
- Butt width is **UNDERREPORTED by 2.4x** (reports 82mm, should be ~35mm)
- Butt thickness is **IMPOSSIBLE** (reports 34.65mm, but entire axe is only 15mm thick!)
- This makes tallone_spessore > total_thickness, which is physically impossible

### Error #2: Incavo (Socket) Detection

**Location:** Lines 181-352 in `_detect_socket()`

**Current Code Logic:**
```python
# Line 199: Filters "top surface"
y_threshold = np.percentile(butt_vertices_pca[:, 1], 75)
top_surface_mask = butt_vertices_pca[:, 1] >= y_threshold

# Lines 245-247: Measures socket depth
y_min = top_vertices[:, 1].min()
y_max = top_vertices[:, 1].max()
depth_range = y_max - y_min

# Lines 312-313: Measures socket width
x_range = socket_vertices[:, 0].max() - socket_vertices[:, 0].min()
z_range = socket_vertices[:, 2].max() - socket_vertices[:, 2].min()
```

**The Problem:**
1. **Wrong surface selection**: Filters Y > 75th percentile, thinking Y is thickness (vertical)
   - But Y is actually WIDTH (56mm horizontal)
   - So it's selecting the LEFT or RIGHT side of the axe, not the TOP!

2. **Wrong depth measurement**: Measures Y range as depth
   - Y is width (horizontal), so measuring left-to-right variation
   - Should measure Z range (actual vertical/thickness direction)

3. **Wrong width measurement**: Measures X and Z ranges
   - X is length (163mm) - socket can't span the whole axe length!
   - Result: 28.02mm width (because it spans from butt toward middle)
   - Real socket width should be 3-9mm (small rectangular cavity)

**Current Results:**
```
incavo_larghezza = 28.02mm   ← Measures X range (length direction span)
incavo_profondita = 5.12mm   ← Measures Y range (width direction variation)
```

**What It SHOULD Measure:**
```
incavo_larghezza should be X or Y range of socket cluster = 3-9mm
incavo_profondita should be Z range (actual depth into surface) = 7.79mm
```

**Impact:**
- Socket width is **OVERREPORTED by 3-4x** (28mm vs actual 3-9mm)
- Socket depth is **UNDERREPORTED by 1.5x** (5mm vs actual 7.79mm)
- Socket is found on wrong surface (side vs top of butt)

### Error #3: Width Measurement Inconsistency

**Location:** Lines 435-502 in `analyze_body()` and line 530 in `analyze_blade()`

**Current Measurements:**
```
larghezza_minima (min width): 117.28mm
tallone_larghezza (butt width): 82.44mm
tagliente_larghezza (blade width): 85.78mm
```

**The Problem:**
- Minimum width is LARGER than both butt and blade widths!
- This is logically impossible - minimum must be ≤ all other widths

**Root Cause:**
```python
# Line 474: Body width measured as X range
width = section_vertices[:, 0].max() - section_vertices[:, 0].min()

# Line 530: Blade width measured as X range
tagliente_larghezza = (blade_vertices_pca[:, 0].max() -
                       blade_vertices_pca[:, 0].min())
```

- Body measures X range across ENTIRE middle section = ~117mm
- But butt/blade only measure their END sections = ~82-85mm
- Since X is LENGTH, not width, body naturally spans more length!

**What It SHOULD Measure:**
- All widths should use Y range (actual width axis)
- Then minimum width would correctly be less than blade/butt widths

### Error #4: Body Thickness Measurements

**Location:** Lines 479-492 in `analyze_body()`

**Current Code:**
```python
# Lines 480-481: Thickness with margins
spessore_max_con_margini = (body_vertices_pca[:, 1].max() -
                            body_vertices_pca[:, 1].min())

# Lines 489-490: Thickness without margins
spessore_max_senza_margini = (central_body[:, 1].max() -
                              central_body[:, 1].min())
```

**Current Results:**
```
spessore_massimo_con_margini = 56.28mm
spessore_massimo_senza_margini = 42.67mm
```

**The Problem:**
- These are measuring Y range, which is WIDTH (56mm), not thickness!
- Actual thickness is only 15mm
- Reporting body thickness as 56mm is physically impossible

**What It SHOULD Measure:**
```
spessore should use Z range (actual thickness axis) ≈ 15mm
```

---

## Part 3: Summary of All Coordinate Confusions

| Feature | Current Axis | Current Value | Correct Axis | Expected Value | Error Ratio |
|---------|-------------|---------------|--------------|----------------|-------------|
| Tallone larghezza | X (length) | 82.44mm | Y (width) | ~35-40mm | 2.0x over |
| Tallone spessore | Y (width) | 34.65mm | Z (thickness) | ~1.5mm | 23x over! |
| Incavo larghezza | X (length span) | 28.02mm | Y or X (local) | 3-9mm | 3-4x over |
| Incavo profondita | Y (width var) | 5.12mm | Z (depth) | 7.79mm | 1.5x under |
| Larghezza minima | X (length) | 117.28mm | Y (width) | ~30-40mm | 3x over |
| Body spessore | Y (width) | 56.28mm | Z (thickness) | ~15mm | 3.7x over |
| Tagliente larghezza | X (length) | 85.78mm | Y (width) | ~40-50mm | 1.7x over |

---

## Part 4: The Correct Coordinate System

Based on PCA analysis of axe974.obj:

```
CORRECT MAPPING (after PCA transform):
===========================================
X axis (vertices_pca[:, 0]):
  Range: -74.39 to +88.89 mm (163.29mm total)
  → LONGEST dimension
  → LENGTH of axe (butt to blade direction)
  → Butt at X-positive, Blade at X-negative

Y axis (vertices_pca[:, 1]):
  Range: -28.34 to +27.94 mm (56.28mm total)
  → MEDIUM dimension
  → WIDTH of axe (left to right)
  → Lateral spread

Z axis (vertices_pca[:, 2]):
  Range: -7.60 to +7.58 mm (15.19mm total)
  → SHORTEST dimension
  → THICKNESS of axe (top to bottom)
  → Socket should be detected here
```

**Note:** The code correctly identifies butt_end and blade_end using Z values (lines 77-83), but then incorrectly assumes Z is the length axis everywhere else!

---

## Part 5: Required Fixes

### Fix Strategy

**Option A: Update ALL measurements to use correct axes**
- Change every X→Y, Y→Z, Z→X throughout the code
- Update documentation to match reality
- Risk: High complexity, many changes

**Option B: Fix the PCA transform to match documentation**
- Reorder PCA components so Z is longest, X is medium, Y is shortest
- Keep all measurement code the same
- Risk: May break other assumptions

**Recommendation: Option A** - Fix measurements to match PCA reality
- PCA is mathematically sound (orders by variance)
- Changing measurements is clearer and more maintainable
- Easier to verify correctness

### Specific Code Changes Needed

#### 1. Fix Tallone Measurements (lines 151-162)
```python
# CURRENT (WRONG):
tallone_larghezza = x_values.max() - x_values.min()  # X is length!
tallone_spessore = y_values.max() - y_values.min()   # Y is width!

# CORRECTED:
tallone_larghezza = y_values.max() - y_values.min()  # Y is width
tallone_spessore = z_values.max() - z_values.min()   # Z is thickness
```

#### 2. Fix Socket Detection Surface (lines 198-200)
```python
# CURRENT (WRONG):
y_threshold = np.percentile(butt_vertices_pca[:, 1], 75)  # Y is width!
top_surface_mask = butt_vertices_pca[:, 1] >= y_threshold

# CORRECTED:
z_threshold = np.percentile(butt_vertices_pca[:, 2], 75)  # Z is thickness
top_surface_mask = butt_vertices_pca[:, 2] >= z_threshold
```

#### 3. Fix Socket Depth Measurement (lines 245-247)
```python
# CURRENT (WRONG):
y_min = top_vertices[:, 1].min()
y_max = top_vertices[:, 1].max()
depth_range = y_max - y_min

# CORRECTED:
z_min = top_vertices[:, 2].min()
z_max = top_vertices[:, 2].max()
depth_range = z_max - z_min
```

#### 4. Fix Socket Width Measurement (lines 228, 291-326)
```python
# CURRENT (WRONG):
# Uses Y deviations for curvature (line 228)
deviations = neighbors[:, 1] - centroid[1]

# Measures X and Z ranges for socket (lines 312-313)
x_range = socket_vertices[:, 0].max() - socket_vertices[:, 0].min()
z_range = socket_vertices[:, 2].max() - socket_vertices[:, 2].min()

# CORRECTED:
# Use Z deviations for curvature (vertical depth changes)
deviations = neighbors[:, 2] - centroid[2]

# Measure X and Y ranges for socket (in top surface plane)
x_range = socket_vertices[:, 0].max() - socket_vertices[:, 0].min()
y_range = socket_vertices[:, 1].max() - socket_vertices[:, 1].min()
```

#### 5. Fix Body Width Measurements (lines 474, 530)
```python
# CURRENT (WRONG):
width = section_vertices[:, 0].max() - section_vertices[:, 0].min()  # X is length!

# CORRECTED:
width = section_vertices[:, 1].max() - section_vertices[:, 1].min()  # Y is width
```

#### 6. Fix Body Thickness Measurements (lines 480-481, 489-490)
```python
# CURRENT (WRONG):
spessore_max_con_margini = (body_vertices_pca[:, 1].max() -
                            body_vertices_pca[:, 1].min())  # Y is width!

# CORRECTED:
spessore_max_con_margini = (body_vertices_pca[:, 2].max() -
                            body_vertices_pca[:, 2].min())  # Z is thickness
```

#### 7. Update Documentation (lines 61-64)
```python
# CURRENT (WRONG):
"""
Convenzione:
- Asse Z: lunghezza ascia (tallone -> tagliente)
- Asse X: larghezza
- Asse Y: spessore
"""

# CORRECTED:
"""
Convenzione PCA (automatica, ordinata per varianza):
- Asse X (PCA componente 0): lunghezza ascia (tallone -> tagliente) [163mm]
- Asse Y (PCA componente 1): larghezza (sinistra -> destra) [56mm]
- Asse Z (PCA componente 2): spessore (basso -> alto) [15mm]

Nota: La PCA ordina automaticamente per varianza decrescente.
"""
```

#### 8. Fix Butt/Blade Orientation Detection (lines 77-86)
```python
# CURRENT (WRONG - uses Z for orientation but Z is thickness!):
z_values = self.vertices_pca[:, 2]
self.z_min, self.z_max = z_values.min(), z_values.max()
self.butt_end = self.z_max
self.blade_end = self.z_min

# CORRECTED (use X for length orientation):
x_values = self.vertices_pca[:, 0]
self.x_min, self.x_max = x_values.min(), x_values.max()
self.butt_end = self.x_max  # Positive X end
self.blade_end = self.x_min  # Negative X end
```

#### 9. Update All Region Filters Throughout

**Current pattern (WRONG):**
```python
# Uses Z for length-based filtering
butt_mask = self.vertices_pca[:, 2] >= butt_threshold
blade_mask = self.vertices_pca[:, 2] <= blade_threshold
body_mask = (self.vertices_pca[:, 2] >= body_start) & (...)
```

**Corrected pattern:**
```python
# Use X for length-based filtering
butt_mask = self.vertices_pca[:, 0] >= butt_threshold
blade_mask = self.vertices_pca[:, 0] <= blade_threshold
body_mask = (self.vertices_pca[:, 0] >= body_start) & (...)
```

**All affected lines:**
- Line 140-141 (butt region)
- Line 367-369 (central region for edges)
- Line 448-453 (body region)
- Line 519-520 (blade region)
- Line 538-539 (body for blade comparison)
- Line 551-553 (blade edge)

---

## Part 6: Verification Tests

After fixes, verify with axe974:

### Expected Measurements:
```
✓ Length: 163.28mm (unchanged)
✓ Width: 56.28mm (unchanged)
✓ Thickness: 15.19mm (unchanged)

✓ Tallone larghezza: ~35-40mm (was 82.44mm)
✓ Tallone spessore: ~1.5-2mm (was 34.65mm)

✓ Incavo larghezza: 3-9mm (was 28.02mm)
✓ Incavo profondita: ~7.79mm (was 5.12mm)

✓ Larghezza minima: ~30-40mm (was 117.28mm)
✓ Tagliente larghezza: ~40-50mm (was 85.78mm)

✓ Body spessore: ~15mm (was 56.28mm)
```

### Logic Tests:
- [ ] tallone_spessore < total thickness (15mm)
- [ ] incavo_larghezza < tallone_larghezza
- [ ] incavo_profondita < tallone_spessore
- [ ] larghezza_minima ≤ min(tallone_larghezza, tagliente_larghezza)
- [ ] All "spessore" measurements ≤ 15mm

---

## Conclusion

The morphometric measurement system has a **fundamental coordinate system error** that invalidates nearly all measurements. The code documentation claims one axis mapping, but the PCA transformation produces the opposite. This causes:

1. All thickness measurements to report width values (3-4x too large)
2. Socket width to be measured along the wrong axis (3-4x too large)
3. Socket to be detected on the wrong surface (side instead of top)
4. Width measurements to report length values (2-3x too large)

**All measurements must be systematically corrected** by swapping axis indices throughout the code. The fixes are straightforward but must be applied consistently across ~15 locations in the file.

---

## Files to Modify

- `/Users/enzo/Documents/BrozeAXE-AI/archaeological-classifier/acs/savignano/morphometric_extractor.py` (primary file)

## Testing

Run with axe974.obj after fixes:
```bash
python test_axe974_report.py
```

---

**Report End**
