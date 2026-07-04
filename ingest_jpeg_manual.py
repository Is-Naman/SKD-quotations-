#!/usr/bin/env python3
"""
Manual ingestion of products from JPEG uploads that cannot be OCR'd.
Data read directly from the images by human/AI inspection.
"""
import csv
import re
import sys
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

CATALOG = Path(r'c:\Users\Asus\Documents\LP of SKD\catalogs\master_product_catalog_clean.csv')

# =====================================================================
# Products extracted from JPEG images
# =====================================================================
JPEG_PRODUCTS = [
    # -----------------------------------------------------------------
    # Anchor Roma 2026.jpeg — Anchor Price List W.E.F April 2026
    # -----------------------------------------------------------------
    # Anchor Roma column (MRP prices)
    ("Anchor Roma 6A 1 Way Switch", 77, "pcs"),
    ("Anchor Roma 6A 2 Way Switch", 186, "pcs"),
    ("Anchor Roma 16A 1 Way Switch", 206, "pcs"),
    ("Anchor Roma 16A 1 Way Switch Neon", 245, "pcs"),
    ("Anchor Roma 16A 2 Way Switch", 235, "pcs"),
    ("Anchor Roma Bell Push 1M", 193, "pcs"),
    ("Anchor Roma Bell Push 2M", 221, "pcs"),
    ("Anchor Roma 25A SP Switch Neon 1M", 314, "pcs"),
    ("Anchor Roma 32A DP Switch Neon 2M", 406, "pcs"),
    ("Anchor Roma 10A 3 Pin Socket", 179, "pcs"),
    ("Anchor Roma 20A Socket", 319, "pcs"),
    ("Anchor Roma Fan Regulator 1M", 441, "pcs"),
    ("Anchor Roma Fan Regulator 2M", 616, "pcs"),
    ("Anchor Roma TV Socket", 204, "pcs"),
    ("Anchor Roma USB Socket 1M", 1480, "pcs"),
    ("Anchor Roma RJ11 Telephone Socket", 204, "pcs"),
    ("Anchor Roma RJ45 CAT6 Socket", 842, "pcs"),
    ("Anchor Roma Indicator", 143, "pcs"),
    ("Anchor Roma Blank Plate", 45, "pcs"),
    ("Anchor Roma Foot Lamp 3M", 780, "pcs"),
    ("Anchor Roma 6-32A SP Mini MCB", 365, "pcs"),
    ("Anchor Roma 1M Plate", 149, "pcs"),
    ("Anchor Roma 2M Plate", 149, "pcs"),
    ("Anchor Roma 3M Plate", 191, "pcs"),
    ("Anchor Roma 4M Plate", 223, "pcs"),
    ("Anchor Roma 6M Plate", 307, "pcs"),
    ("Anchor Roma 8M Plate", 392, "pcs"),
    ("Anchor Roma 8M Vertical Plate", 392, "pcs"),
    ("Anchor Roma 12M Plate", 485, "pcs"),
    ("Anchor Roma 16M Plate", 545, "pcs"),
    ("Anchor Roma 18M Plate", 570, "pcs"),
    # Modular boxes (Metal)
    ("Anchor Roma 1-2 Modular Metal Gang Box", 73, "pcs"),
    ("Anchor Roma 3M Modular Metal Gang Box", 100, "pcs"),
    ("Anchor Roma 4M Modular Metal Gang Box", 121, "pcs"),
    ("Anchor Roma 6M Modular Metal Gang Box", 162, "pcs"),
    ("Anchor Roma 8M Modular Metal Gang Box", 207, "pcs"),
    ("Anchor Roma 12M Modular Metal Gang Box", 256, "pcs"),
    ("Anchor Roma 16M Modular Metal Gang Box", 293, "pcs"),
    ("Anchor Roma 18M Modular Metal Gang Box", 325, "pcs"),

    # -----------------------------------------------------------------
    # Schneider LP April 26.jpeg — MCB Acti9 (1st APRIL 2026)
    # -----------------------------------------------------------------
    # MCB xC60 "C Curve"
    ("Schneider MCB 1-4A 1 Pole xC60", 820, "pcs"),
    ("Schneider MCB 6-32A 1 Pole xC60", 486, "pcs"),
    ("Schneider MCB 40A 1 Pole xC60", 1161, "pcs"),
    ("Schneider MCB 63A 1 Pole xC60", 1177, "pcs"),
    ("Schneider MCB 1-4A 2 Pole xC60", 2570, "pcs"),
    ("Schneider MCB 6-32A 2 Pole xC60", 1615, "pcs"),
    ("Schneider MCB 40A 2 Pole xC60", 2599, "pcs"),
    ("Schneider MCB 63A 2 Pole xC60", 2621, "pcs"),
    ("Schneider MCB 1-4A 3 Pole xC60", 3528, "pcs"),
    ("Schneider MCB 6-32A 3 Pole xC60", 2678, "pcs"),
    ("Schneider MCB 40A 3 Pole xC60", 4079, "pcs"),
    ("Schneider MCB 63A 3 Pole xC60", 4214, "pcs"),
    ("Schneider MCB 1-4A 4 Pole xC60", 4440, "pcs"),
    ("Schneider MCB 6-32A 4 Pole xC60", 3609, "pcs"),
    ("Schneider MCB 40A 4 Pole xC60", 5243, "pcs"),
    ("Schneider MCB 63A 4 Pole xC60", 5460, "pcs"),
    # MCB C120N
    ("Schneider MCB 80A 1 Pole C120N", 3787, "pcs"),
    ("Schneider MCB 100A 1 Pole C120N", 4248, "pcs"),
    ("Schneider MCB 125A 1 Pole C120N", 4675, "pcs"),
    ("Schneider MCB 80A 2 Pole C120N", 9787, "pcs"),
    ("Schneider MCB 100A 2 Pole C120N", 8952, "pcs"),
    ("Schneider MCB 125A 2 Pole C120N", 9840, "pcs"),
    ("Schneider MCB 80A 3 Pole C120N", 13184, "pcs"),
    ("Schneider MCB 100A 3 Pole C120N", 14051, "pcs"),
    ("Schneider MCB 125A 3 Pole C120N", 15585, "pcs"),
    ("Schneider MCB 80A 4 Pole C120N", 17181, "pcs"),
    ("Schneider MCB 100A 4 Pole C120N", 17901, "pcs"),
    ("Schneider MCB 125A 4 Pole C120N", 20260, "pcs"),
    # SPN DB
    ("Schneider SPN DB 6W A9HSND", 3429, "pcs"),
    ("Schneider SPN DB 8W A9HSND", 3738, "pcs"),
    ("Schneider SPN DB 12W A9HSND", 4495, "pcs"),
    ("Schneider SPN DB 18W A9HSND", 6022, "pcs"),
    # TPN DB
    ("Schneider TPN DB 4W A9HTND", 9024, "pcs"),
    ("Schneider TPN DB 6W A9HTND", 9159, "pcs"),
    ("Schneider TPN DB 8W A9HTND", 11294, "pcs"),
    ("Schneider TPN DB 12W A9HTND", 17242, "pcs"),
    # RCCB Acti9
    ("Schneider RCCB 25A 2 Pole 30mA", 5571, "pcs"),
    ("Schneider RCCB 40A 2 Pole 30mA", 6558, "pcs"),
    ("Schneider RCCB 63A 2 Pole 30mA", 7897, "pcs"),
    ("Schneider RCCB 25A 2 Pole 100mA", 6183, "pcs"),
    ("Schneider RCCB 40A 2 Pole 100mA", 7070, "pcs"),
    ("Schneider RCCB 63A 2 Pole 100mA", 8492, "pcs"),
    ("Schneider RCCB 25A 2 Pole 300mA", 6371, "pcs"),
    ("Schneider RCCB 40A 2 Pole 300mA", 7415, "pcs"),
    ("Schneider RCCB 63A 2 Pole 300mA", 8663, "pcs"),
    ("Schneider RCCB 25A 4 Pole 30mA", 7819, "pcs"),
    ("Schneider RCCB 40A 4 Pole 30mA", 8310, "pcs"),
    ("Schneider RCCB 63A 4 Pole 30mA", 8555, "pcs"),
    ("Schneider RCCB 25A 4 Pole 100mA", 9774, "pcs"),
    ("Schneider RCCB 40A 4 Pole 100mA", 9621, "pcs"),
    ("Schneider RCCB 63A 4 Pole 100mA", 11141, "pcs"),
    ("Schneider RCCB 25A 4 Pole 300mA", 10388, "pcs"),
    ("Schneider RCCB 40A 4 Pole 300mA", 10445, "pcs"),
    ("Schneider RCCB 63A 4 Pole 300mA", 12340, "pcs"),
    # Compact RCBO
    ("Schneider RCBO 6-32A 30mA DPN N Vigi", 8601, "pcs"),
    ("Schneider RCBO 40A 30mA DPN N Vigi", 10882, "pcs"),
    ("Schneider RCBO 6-32A 300mA DPN N Vigi", 8736, "pcs"),
    ("Schneider RCBO 40A 300mA DPN N Vigi", 11071, "pcs"),
    ("Schneider RCBO 63A 4P 30mA Block for MCB", 12505, "pcs"),
    # D Curve MCB Acti9
    ("Schneider D Curve MCB 6-32A 1 Pole", 698, "pcs"),
    ("Schneider D Curve MCB 40A 1 Pole", 1254, "pcs"),
    ("Schneider D Curve MCB 63A 1 Pole", 1268, "pcs"),
    ("Schneider D Curve MCB 6-32A 2 Pole", 1692, "pcs"),
    ("Schneider D Curve MCB 40A 2 Pole", 2747, "pcs"),
    ("Schneider D Curve MCB 63A 2 Pole", 2780, "pcs"),
    ("Schneider D Curve MCB 6-32A 3 Pole", 2821, "pcs"),
    ("Schneider D Curve MCB 40A 3 Pole", 4322, "pcs"),
    ("Schneider D Curve MCB 63A 3 Pole", 5014, "pcs"),
    ("Schneider D Curve MCB 6-32A 4 Pole", 3742, "pcs"),
    ("Schneider D Curve MCB 40A 4 Pole", 5419, "pcs"),
    ("Schneider D Curve MCB 63A 4 Pole", 5475, "pcs"),
    # Plug Socket DB
    ("Schneider 20A DP Plug Socket DB", 3693, "pcs"),
    ("Schneider 32A TP Plug Socket DB", 7349, "pcs"),
    # MCB Enclosure
    ("Schneider MCB Enclosure 2 Pole", 1233, "pcs"),
    ("Schneider MCB Enclosure 4 Pole", 1233, "pcs"),
    # Isolator Acti9
    ("Schneider Isolator 40A 2 Pole Acti9", 1079, "pcs"),
    ("Schneider Isolator 63A 2 Pole Acti9", 1426, "pcs"),
    ("Schneider Isolator 40A 4 Pole Acti9", 2386, "pcs"),
    ("Schneider Isolator 63A 4 Pole Acti9", 2598, "pcs"),
    ("Schneider Isolator 100A 4 Pole Acti9", 4347, "pcs"),
    # 7 Segment DB
    ("Schneider 7 Segment DB 4W", 17964, "pcs"),
    ("Schneider 7 Segment DB 6W", 20086, "pcs"),
    ("Schneider 7 Segment DB 8W", 22428, "pcs"),
    ("Schneider 7 Segment DB 12W", 28154, "pcs"),
    # Flexy Tier DB
    ("Schneider Flexy Tier DB 2R 24M", 9671, "pcs"),
    ("Schneider Flexy Tier DB 3R 36M", 11615, "pcs"),
    ("Schneider Flexy Tier DB 4R 40M", 13271, "pcs"),
    ("Schneider Flexy Tier DB 4R 56M", 12825, "pcs"),
    # MCCB EasyPact CVS (25kA 3 Pole - from April image)
    ("Schneider MCCB 16-63A 3 Pole 25kA EasyPact CVS", 11570, "pcs"),
    ("Schneider MCCB 100A 3 Pole 25kA EasyPact CVS", 11640, "pcs"),
    ("Schneider MCCB 125A 3 Pole 25kA EasyPact CVS", 17030, "pcs"),
    ("Schneider MCCB 160A 3 Pole 25kA EasyPact CVS", 22220, "pcs"),
    ("Schneider MCCB 200A 3 Pole 25kA EasyPact CVS", 29410, "pcs"),
    ("Schneider MCCB 250A 3 Pole 25kA EasyPact CVS", 34420, "pcs"),
    # MCCB 4 Pole
    ("Schneider MCCB 16-63A 4 Pole 25kA EasyPact CVS", 16100, "pcs"),
    ("Schneider MCCB 125A 4 Pole 25kA EasyPact CVS", 20840, "pcs"),
    ("Schneider MCCB 160A 4 Pole 25kA EasyPact CVS", 26630, "pcs"),
    ("Schneider MCCB 200A 4 Pole 25kA EasyPact CVS", 36770, "pcs"),
    ("Schneider MCCB 250A 4 Pole 25kA EasyPact CVS", 42110, "pcs"),

    # -----------------------------------------------------------------
    # Schneider LP April 26 B.jpeg — Contactors, Overload Relays, etc.
    # -----------------------------------------------------------------
    # Tesys D Contactor
    ("Schneider Contactor 9A AC3 Tesys D AC", 2725, "pcs"),
    ("Schneider Contactor 12A AC3 Tesys D AC", 3070, "pcs"),
    ("Schneider Contactor 18A AC3 Tesys D AC", 3560, "pcs"),
    ("Schneider Contactor 25A AC3 Tesys D AC", 4420, "pcs"),
    ("Schneider Contactor 32A AC3 Tesys D AC", 8600, "pcs"),
    ("Schneider Contactor 38A AC3 Tesys D AC", 12230, "pcs"),
    ("Schneider Contactor 40A AC3 Tesys D AC", 13085, "pcs"),
    ("Schneider Contactor 50A AC3 Tesys D AC", 16960, "pcs"),
    ("Schneider Contactor 65A AC3 Tesys D AC", 23535, "pcs"),
    ("Schneider Contactor 80A AC3 Tesys D AC", 29420, "pcs"),
    ("Schneider Contactor 95A AC3 Tesys D AC", 37885, "pcs"),
    ("Schneider Contactor 115A AC3 Tesys D AC", 48530, "pcs"),
    ("Schneider Contactor 150A AC3 Tesys D AC", 51605, "pcs"),
    # Tesys K Mini Contactor
    ("Schneider Mini Contactor 6A Tesys K AC", 2315, "pcs"),
    ("Schneider Mini Contactor 9A Tesys K AC", 2420, "pcs"),
    ("Schneider Mini Contactor 12A Tesys K AC", 2740, "pcs"),
    ("Schneider Mini Contactor 16A Tesys K AC", 3240, "pcs"),
    # Contactor Easypact TVS
    ("Schneider Contactor 6A EasyPact TVS", 1980, "pcs"),
    ("Schneider Contactor 9A EasyPact TVS", 2030, "pcs"),
    ("Schneider Contactor 12A EasyPact TVS", 2320, "pcs"),
    ("Schneider Contactor 18A EasyPact TVS", 2675, "pcs"),
    ("Schneider Contactor 25A EasyPact TVS", 3640, "pcs"),
    ("Schneider Contactor 32A EasyPact TVS", 7635, "pcs"),
    ("Schneider Contactor 38A EasyPact TVS", 8905, "pcs"),
    ("Schneider Contactor 40A EasyPact TVS", 11950, "pcs"),
    ("Schneider Contactor 50A EasyPact TVS", 14540, "pcs"),
    ("Schneider Contactor 65A EasyPact TVS", 19700, "pcs"),
    ("Schneider Contactor 80A EasyPact TVS", 25625, "pcs"),
    ("Schneider Contactor 95A EasyPact TVS", 30705, "pcs"),
    ("Schneider Contactor 120A EasyPact TVS", 36580, "pcs"),
    ("Schneider Contactor 150A EasyPact TVS", 43345, "pcs"),
    ("Schneider Contactor 160A EasyPact TVS", 48300, "pcs"),
    ("Schneider Contactor 200A EasyPact TVS", 66485, "pcs"),
    # LRE Overload Relay
    ("Schneider LRE Overload Relay 0.4-0.63A", 2435, "pcs"),
    ("Schneider LRE Overload Relay 0.63-1.0A", 2435, "pcs"),
    ("Schneider LRE Overload Relay 1.0-1.6A", 2435, "pcs"),
    ("Schneider LRE Overload Relay 1.6-2.5A", 2435, "pcs"),
    ("Schneider LRE Overload Relay 2.5-4A", 2435, "pcs"),
    ("Schneider LRE Overload Relay 4-6A", 2435, "pcs"),
    ("Schneider LRE Overload Relay 5.5-8A", 2435, "pcs"),
    ("Schneider LRE Overload Relay 7-10A", 2435, "pcs"),
    ("Schneider LRE Overload Relay 9-13A", 2435, "pcs"),
    ("Schneider LRE Overload Relay 12-18A", 2695, "pcs"),
    ("Schneider LRE Overload Relay 16-24A", 3115, "pcs"),
    ("Schneider LRE Overload Relay 23-32A", 4165, "pcs"),
    # GV2 MPCB Thermal Magnetic (Push Button)
    ("Schneider GV2 MPCB 0.25-0.4A Push Button", 8175, "pcs"),
    ("Schneider GV2 MPCB 0.4-0.63A Push Button", 8710, "pcs"),
    ("Schneider GV2 MPCB 0.63-1.0A Push Button", 8895, "pcs"),
    ("Schneider GV2 MPCB 1.0-1.6A Push Button", 8895, "pcs"),
    ("Schneider GV2 MPCB 1.6-2.5A Push Button", 8895, "pcs"),
    ("Schneider GV2 MPCB 2.5-4A Push Button", 9205, "pcs"),
    ("Schneider GV2 MPCB 4-6.3A Push Button", 9205, "pcs"),
    ("Schneider GV2 MPCB 6-10A Push Button", 9205, "pcs"),
    ("Schneider GV2 MPCB 9-14A Push Button", 10310, "pcs"),
    ("Schneider GV2 MPCB 13-18A Push Button", 11105, "pcs"),
    ("Schneider GV2 MPCB 17-23A Push Button", 11855, "pcs"),
    ("Schneider GV2 MPCB 20-25A Push Button", 11855, "pcs"),
    ("Schneider GV2 MPCB 24-32A Push Button", 19205, "pcs"),
    # Capacitor Duty Contactor
    ("Schneider Capacitor Duty Contactor 12.5kVar", 7565, "pcs"),
    ("Schneider Capacitor Duty Contactor 16.7kVar", 10625, "pcs"),
    ("Schneider Capacitor Duty Contactor 20kVar", 11935, "pcs"),
    ("Schneider Capacitor Duty Contactor 25kVar", 13090, "pcs"),
    ("Schneider Capacitor Duty Contactor 32kVar", 28520, "pcs"),
    ("Schneider Capacitor Duty Contactor 40kVar", 39290, "pcs"),
    ("Schneider Capacitor Duty Contactor 60kVar", 44230, "pcs"),
    # Capacitor Varplus Can Heavy Duty
    ("Schneider Capacitor Varplus 5kVar", 3862, "pcs"),
    ("Schneider Capacitor Varplus 7.5kVar", 5661, "pcs"),
    ("Schneider Capacitor Varplus 10kVar", 7046, "pcs"),
    ("Schneider Capacitor Varplus 12.5kVar", 8848, "pcs"),
    ("Schneider Capacitor Varplus 15kVar", 10565, "pcs"),
    ("Schneider Capacitor Varplus 20kVar", 14090, "pcs"),
    ("Schneider Capacitor Varplus 25kVar", 17609, "pcs"),
    ("Schneider Capacitor Varplus 30kVar", 21231, "pcs"),
    ("Schneider Capacitor Varplus 40kVar", 27578, "pcs"),
    ("Schneider Capacitor Varplus 50kVar", 34313, "pcs"),
    # Digital Meters
    ("Schneider Ammeter 1 Phase DM1110", 1587, "pcs"),
    ("Schneider Ammeter 3 Phase DM3110", 2525, "pcs"),
    ("Schneider Voltmeter 1 Phase DM1210", 1587, "pcs"),
    ("Schneider Voltmeter 3 Phase DM3210", 2525, "pcs"),
    ("Schneider VAF+PF Meter w/o Port DM6100", 3827, "pcs"),
    ("Schneider VAF+PF Meter RS485 DM6300", 4848, "pcs"),
    ("Schneider Energy Meter w/o Port EM1000", 4175, "pcs"),
    ("Schneider Energy Meter RS485 EM1200", 5067, "pcs"),

    # -----------------------------------------------------------------
    # Siemens New LP.jpeg — Siemens Short List April 2026
    # (Very dense — key products only)
    # -----------------------------------------------------------------
    # 3TF Contactors (AC coil)
    ("Siemens Contactor 3TF30 AC 9A", 2965, "pcs"),
    ("Siemens Contactor 3TF31 AC 12A", 2905, "pcs"),
    ("Siemens Contactor 3TF32 AC 16A", 3080, "pcs"),
    ("Siemens Contactor 3TF33 AC 18A", 4115, "pcs"),
    ("Siemens Contactor 3TF34 AC 22A", 9445, "pcs"),
    ("Siemens Contactor 3TF35 AC 25A", 13695, "pcs"),
    ("Siemens Contactor 3TF46 AC 32A", 18905, "pcs"),
    ("Siemens Contactor 3TF47 AC 36A", 26855, "pcs"),
    ("Siemens Contactor 3TF48 AC 50A", 34405, "pcs"),
    ("Siemens Contactor 3TF49 AC 63A", 42880, "pcs"),
    ("Siemens Contactor 3TF50 AC 80A", 51315, "pcs"),
    ("Siemens Contactor 3TF51 AC 100A", 67675, "pcs"),
    ("Siemens Contactor 3TF52 AC 110A", 83820, "pcs"),
    ("Siemens Contactor 3TF53 AC 130A", 90890, "pcs"),
    ("Siemens Contactor 3TF54 AC 150A", 110680, "pcs"),
    ("Siemens Contactor 3TF55 AC 170A", 137015, "pcs"),
    ("Siemens Contactor 3TF56 AC 200A", 160675, "pcs"),
    ("Siemens Contactor 3TF57 AC 250A", 375000, "pcs"),
    # MPCB 3RV2011-2041
    ("Siemens MPCB 3RV2011 0.1-0.4A", 8020, "pcs"),
    ("Siemens MPCB 3RV2011 0.4-0.6A", 9030, "pcs"),
    ("Siemens MPCB 3RV2011 0.6-1A", 9380, "pcs"),
    ("Siemens MPCB 3RV2011 1-2.4A", 9470, "pcs"),
    ("Siemens MPCB 3RV2011 2-6A", 9550, "pcs"),
    ("Siemens MPCB 3RV2011 5-10A", 9650, "pcs"),
    ("Siemens MPCB 3RV2011 8-13A", 10590, "pcs"),
    ("Siemens MPCB 3RV2011 10-16A", 11080, "pcs"),
    ("Siemens MPCB 3RV2011 14-20A", 11290, "pcs"),
    ("Siemens MPCB 3RV2011 18-25A", 11225, "pcs"),
    # 3UA Overload Relays (ML1 OLR and ML2 OLR)
    ("Siemens Overload Relay 3UA ML1 16A", 4510, "pcs"),
    ("Siemens Overload Relay 3UA ML1 42A", 4510, "pcs"),
    ("Siemens Overload Relay 3UA ML2 2-10A", 6670, "pcs"),
    # MCCB 3VM
    ("Siemens MCCB 3VM 16-63A 25K 3 Pole", 19050, "pcs"),
    ("Siemens MCCB 3VM 100A 25K 3 Pole", 19050, "pcs"),
    ("Siemens MCCB 3VM 125A 25K 3 Pole", 24575, "pcs"),
    ("Siemens MCCB 3VM 160A 25K 3 Pole", 33820, "pcs"),
    ("Siemens MCCB 3VM 16-63A 25K 4 Pole", 28700, "pcs"),
    ("Siemens MCCB 3VM 100A 25K 4 Pole", 28700, "pcs"),
    ("Siemens MCCB 3VM 125A 25K 4 Pole", 33640, "pcs"),
    ("Siemens MCCB 3VM 160A 25K 4 Pole", 43050, "pcs"),
    ("Siemens MCCB 3VM 200A 36K 3 Pole", 59420, "pcs"),
    ("Siemens MCCB 3VM 250A 36K 3 Pole", 59420, "pcs"),
    ("Siemens MCCB 3VM 200A 36K 4 Pole", 69345, "pcs"),
    ("Siemens MCCB 3VM 250A 36K 4 Pole", 69345, "pcs"),
    # MCB (Siemens MCB SP 1-4A)
    ("Siemens MCB SP 1-4A", 606, "pcs"),
    ("Siemens MCB 6-32A SP", 376, "pcs"),
    ("Siemens MCB 40A SP", 826, "pcs"),
    ("Siemens MCB 50-63A SP", 950, "pcs"),
    ("Siemens MCB DP 1-4A", 1793, "pcs"),
    ("Siemens MCB 6-32A DP", 1342, "pcs"),
    ("Siemens MCB 40A DP", 1883, "pcs"),
    ("Siemens MCB 50-63A DP", 2210, "pcs"),
    ("Siemens MCB TP 1-4A", 2015, "pcs"),
    ("Siemens MCB 6-32A TP", 2510, "pcs"),
    ("Siemens MCB 40A TP", 2820, "pcs"),
    ("Siemens MCB 50-63A TP", 3149, "pcs"),
    ("Siemens MCB FP 1-4A", 2786, "pcs"),
    ("Siemens MCB 6-32A FP", 3600, "pcs"),
    ("Siemens MCB 40A FP", 3600, "pcs"),
    ("Siemens MCB 50-63A FP", 4168, "pcs"),

    # -----------------------------------------------------------------
    # L&T New LP.jpeg — L&T price list (very dense, key items)
    # (Includes DN2/DN3/DN4 MCCBs, ML Contactors, MCBs, Fuses, etc.)
    # -----------------------------------------------------------------
    # MCCB DN2
    ("L&T MCCB DN2 3P 36K 125A", 24600, "pcs"),
    ("L&T MCCB DN2 3P 36K 160A", 30500, "pcs"),
    ("L&T MCCB DN2 3P 36K 200A", 31600, "pcs"),
    ("L&T MCCB DN2 3P 36K 250A", 33100, "pcs"),
    ("L&T MCCB DN2 3P 36K 320A-400A", 42400, "pcs"),
    ("L&T MCCB DN2 3P 36K 500-630A", 56000, "pcs"),
    ("L&T MCCB DN2 3P 36K 800A 50k", 98900, "pcs"),
    ("L&T MCCB DN2 3P 36K 1000A 50k", 146300, "pcs"),
    # MCB (Exora)
    ("L&T Exora MCB 1-4A 1 Pole", 540, "pcs"),
    ("L&T Exora MCB 6-32A 1 Pole", 318, "pcs"),
    ("L&T Exora MCB 1-4A 2 Pole", 1550, "pcs"),
    ("L&T Exora MCB 6-32A 2 Pole", 1080, "pcs"),
    ("L&T Exora MCB 1-4A 3 Pole", 2255, "pcs"),
    ("L&T Exora MCB 6-32A 3 Pole", 1700, "pcs"),
    ("L&T Exora MCB 1-4A 4 Pole", 2840, "pcs"),
    ("L&T Exora MCB 6-32A 4 Pole", 2355, "pcs"),
    ("L&T MCB 4W Mcb box", 825, "pcs"),
    # ML Contactor
    ("L&T ML Contactor 1.5", 6520, "pcs"),
    ("L&T ML Contactor 2", 12110, "pcs"),
    ("L&T ML Contactor 3", 17860, "pcs"),
    ("L&T ML Contactor 4", 29180, "pcs"),
    ("L&T ML Contactor 6", 46180, "pcs"),
    ("L&T ML Contactor 12", 104540, "pcs"),
    # Exora RCCB
    ("L&T Exora RCCB DP 25A 30mA", 3685, "pcs"),
    ("L&T Exora RCCB DP 25A 100mA", 3910, "pcs"),
    ("L&T Exora RCCB FP 25A 30mA", 5160, "pcs"),
    ("L&T Exora RCCB FP 25A 100mA", 5390, "pcs"),
    ("L&T Exora RCCB FP 25A 300mA", 9270, "pcs"),

    # -----------------------------------------------------------------
    # GOLD Medal Price_list March 26.jpeg
    # -----------------------------------------------------------------
    ("Gold Medal 1&2M Metal Gang Box", 35, "pcs"),
    ("Gold Medal 3M Metal Gang Box", 44.10, "pcs"),
    ("Gold Medal 4M Metal Gang Box", 54.70, "pcs"),
    ("Gold Medal 6M Metal Gang Box", 68.40, "pcs"),
    ("Gold Medal 8M(H) Metal Gang Box", 88.90, "pcs"),
    ("Gold Medal 12M Metal Gang Box", 111.70, "pcs"),
    ("Gold Medal G Guard Pipe 25mm 1.2mm", 48.30, "m"),
    ("Gold Medal Circular Box Intersection 4 Way 25mm", 15.50, "pcs"),
    ("Gold Medal Slip Type Bends 25mm", 6, "pcs"),

    # -----------------------------------------------------------------
    # Industrial Socket Ruchi.jpeg (handwritten)
    # -----------------------------------------------------------------
    ("Ruchi Industrial Plug 16A 3 Pin", 120, "pcs"),
    ("Ruchi Industrial Plug 32A 5 Pin", 265, "pcs"),
    ("Ruchi Industrial Socket 16A 3 Pin", 200, "pcs"),
    ("Ruchi Industrial Socket 32A 5 Pin", 350, "pcs"),

    # -----------------------------------------------------------------
    # Relay Rates Schneider (-64% +GST).jpeg
    # (Schneider LRE Overload Relay prices, already added above)
    # -----------------------------------------------------------------
]


def main():
    # Load existing catalog
    rows = []
    existing_names = set()
    with CATALOG.open('r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
        for r in rows:
            existing_names.add(re.sub(r'\s+', ' ', r['product_name'].strip().lower()))

    print(f"Existing catalog: {len(rows)} products")

    # Add JPEG products
    added = 0
    skipped = 0
    for name, price, unit in JPEG_PRODUCTS:
        key = re.sub(r'\s+', ' ', name.strip().lower())
        if key in existing_names:
            skipped += 1
            continue
        existing_names.add(key)
        rows.append({
            'product_id': f'IMG{len(rows)+1:04d}',
            'product_name': name,
            'latest_price': price,
            'unit': unit,
            'description': 'From uploaded image (manual entry)',
        })
        added += 1

    # Write
    with CATALOG.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Added: {added} products from JPEG images")
    print(f"Skipped (duplicates): {skipped}")
    print(f"Total catalog: {len(rows)} products")
    print(f"Saved to: {CATALOG}")


if __name__ == '__main__':
    main()
