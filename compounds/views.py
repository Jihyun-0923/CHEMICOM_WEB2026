import math
import re

from django.db.models import Q
from django.shortcuts import render
from .models import Compound, Element


FORMULA_TOKEN_RE = re.compile(r'([A-Z][a-z]?|\d+|[()\[\]{}.+-])')
ELEMENT_COLORS = {
    'H': '#64d2ff',
    'He': '#c7f9ff',
    'Li': '#ff7a59',
    'Be': '#9acd32',
    'B': '#ffb5a7',
    'C': '#6b7280',
    'N': '#5b8fff',
    'O': '#ff5f7a',
    'F': '#3ddc97',
    'Ne': '#80d8ff',
    'Na': '#b44cf0',
    'Mg': '#2dd4bf',
    'Al': '#a3a3a3',
    'Si': '#f59e0b',
    'P': '#ff8a3d',
    'S': '#ffd60a',
    'Cl': '#30d158',
    'Ar': '#7dd3fc',
    'K': '#c084fc',
    'Ca': '#ffb020',
    'Cr': '#94a3b8',
    'Mn': '#f472b6',
    'Fe': '#ef4444',
    'Cu': '#b45309',
    'Zn': '#60a5fa',
    'Ag': '#c0c0c0',
    'I': '#8b5cf6',
    'Ba': '#84cc16',
    'Au': '#facc15',
    'Pb': '#64748b',
}


def formula_to_latex(formula):
    tokens = FORMULA_TOKEN_RE.findall(formula)

    if ''.join(tokens) != formula:
        return formula

    latex_parts = []
    for token in tokens:
        if token.isdigit():
            latex_parts.append(f'_{{{token}}}')
        elif re.fullmatch(r'[A-Z][a-z]?', token):
            latex_parts.append(f'\\mathrm{{{token}}}')
        else:
            latex_parts.append(token)

    return ''.join(latex_parts)


def element_color(symbol):
    return ELEMENT_COLORS.get(symbol, '#8e37e8')


def molecule_node(symbol, x, y, radius=28):
    if radius is None:
        radius = 22 if symbol == 'H' else 29

    return {
        'symbol': symbol,
        'name': symbol,
        'count': '',
        'color': element_color(symbol),
        'key': f'{symbol}-{x}-{y}',
        'x': x,
        'y': y,
        'r': radius,
        'badge_x': x + radius - 6,
        'badge_y': y + radius - 6,
    }


def molecule_bond(start, end):
    return {
        'x1': start['x'],
        'y1': start['y'],
        'x2': end['x'],
        'y2': end['y'],
    }


def molecule_bonds(start, end, order=1):
    if order <= 1:
        return [molecule_bond(start, end)]

    dx = end['x'] - start['x']
    dy = end['y'] - start['y']
    length = math.hypot(dx, dy) or 1
    normal_x = -dy / length
    normal_y = dx / length
    offsets = [-7, 7] if order == 2 else [-10, 0, 10]
    bonds = []

    for offset in offsets:
        bonds.append({
            'x1': round(start['x'] + normal_x * offset),
            'y1': round(start['y'] + normal_y * offset),
            'x2': round(end['x'] + normal_x * offset),
            'y2': round(end['y'] + normal_y * offset),
        })

    return bonds


def build_structure_visual(atom_specs, bond_specs):
    nodes_by_key = {}
    nodes = []

    for key, symbol, x, y, radius in atom_specs:
        node = molecule_node(symbol, x, y, radius)
        nodes_by_key[key] = node
        nodes.append(node)

    bonds = []
    for start_key, end_key, order in bond_specs:
        bonds.extend(molecule_bonds(
            nodes_by_key[start_key],
            nodes_by_key[end_key],
            order,
        ))

    return {'nodes': nodes, 'bonds': bonds}


def build_methane_visual():
    return build_structure_visual([
        ('c', 'C', 180, 150, 30),
        ('h1', 'H', 180, 64, 22),
        ('h2', 'H', 286, 150, 22),
        ('h3', 'H', 180, 236, 22),
        ('h4', 'H', 74, 150, 22),
    ], [
        ('c', 'h1', 1), ('c', 'h2', 1), ('c', 'h3', 1), ('c', 'h4', 1),
    ])


def build_carbon_dioxide_visual():
    return build_structure_visual([
        ('o1', 'O', 72, 150, 28),
        ('c', 'C', 180, 150, 30),
        ('o2', 'O', 288, 150, 28),
    ], [
        ('o1', 'c', 2), ('c', 'o2', 2),
    ])


def build_ammonia_visual():
    return build_structure_visual([
        ('n', 'N', 180, 150, 30),
        ('h1', 'H', 180, 64, 22),
        ('h2', 'H', 268, 204, 22),
        ('h3', 'H', 92, 204, 22),
    ], [
        ('n', 'h1', 1), ('n', 'h2', 1), ('n', 'h3', 1),
    ])


def build_hydrogen_peroxide_visual():
    return build_structure_visual([
        ('h1', 'H', 34, 150, 22),
        ('o1', 'O', 118, 150, 30),
        ('o2', 'O', 242, 150, 30),
        ('h2', 'H', 326, 150, 22),
    ], [
        ('h1', 'o1', 1), ('o1', 'o2', 1), ('o2', 'h2', 1),
    ])


def build_acetylene_visual():
    return build_structure_visual([
        ('h1', 'H', 34, 150, 22),
        ('c1', 'C', 122, 150, 29),
        ('c2', 'C', 238, 150, 29),
        ('h2', 'H', 326, 150, 22),
    ], [
        ('h1', 'c1', 1), ('c1', 'c2', 3), ('c2', 'h2', 1),
    ])


def build_ethylene_visual():
    return build_structure_visual([
        ('c1', 'C', 122, 150, 29),
        ('c2', 'C', 238, 150, 29),
        ('h1', 'H', 76, 78, 22),
        ('h2', 'H', 76, 222, 22),
        ('h3', 'H', 284, 78, 22),
        ('h4', 'H', 284, 222, 22),
    ], [
        ('c1', 'c2', 2),
        ('c1', 'h1', 1), ('c1', 'h2', 1),
        ('c2', 'h3', 1), ('c2', 'h4', 1),
    ])


def build_ethane_visual():
    return build_structure_visual([
        ('c1', 'C', 122, 150, 29),
        ('c2', 'C', 238, 150, 29),
        ('h1', 'H', 82, 72, 22),
        ('h2', 'H', 60, 150, 22),
        ('h3', 'H', 82, 228, 22),
        ('h4', 'H', 278, 72, 22),
        ('h5', 'H', 300, 150, 22),
        ('h6', 'H', 278, 228, 22),
    ], [
        ('c1', 'c2', 1),
        ('c1', 'h1', 1), ('c1', 'h2', 1), ('c1', 'h3', 1),
        ('c2', 'h4', 1), ('c2', 'h5', 1), ('c2', 'h6', 1),
    ])


def build_methanol_visual():
    return build_structure_visual([
        ('c', 'C', 120, 150, 29),
        ('o', 'O', 235, 150, 29),
        ('h1', 'H', 120, 68, 22),
        ('h2', 'H', 54, 150, 22),
        ('h3', 'H', 120, 232, 22),
        ('h4', 'H', 318, 150, 22),
    ], [
        ('c', 'o', 1),
        ('c', 'h1', 1), ('c', 'h2', 1), ('c', 'h3', 1),
        ('o', 'h4', 1),
    ])


def build_ethanol_visual():
    c1 = molecule_node('C', 78, 150, 29)
    c2 = molecule_node('C', 180, 150, 29)
    o = molecule_node('O', 282, 150, 29)
    h1 = molecule_node('H', 78, 68, 22)
    h2 = molecule_node('H', 20, 150, 22)
    h3 = molecule_node('H', 78, 232, 22)
    h4 = molecule_node('H', 180, 68, 22)
    h5 = molecule_node('H', 180, 232, 22)
    h6 = molecule_node('H', 338, 150, 22)

    nodes = [c1, c2, o, h1, h2, h3, h4, h5, h6]
    bonds = [
        molecule_bond(c1, c2),
        molecule_bond(c2, o),
        molecule_bond(c1, h1),
        molecule_bond(c1, h2),
        molecule_bond(c1, h3),
        molecule_bond(c2, h4),
        molecule_bond(c2, h5),
        molecule_bond(o, h6),
    ]

    return {'nodes': nodes, 'bonds': bonds}


def build_acetic_acid_visual():
    return build_structure_visual([
        ('c1', 'C', 78, 150, 29),
        ('c2', 'C', 180, 150, 29),
        ('o1', 'O', 180, 66, 27),
        ('o2', 'O', 282, 150, 27),
        ('h1', 'H', 78, 68, 21),
        ('h2', 'H', 20, 150, 21),
        ('h3', 'H', 78, 232, 21),
        ('h4', 'H', 338, 150, 21),
    ], [
        ('c1', 'c2', 1), ('c2', 'o1', 2), ('c2', 'o2', 1),
        ('c1', 'h1', 1), ('c1', 'h2', 1), ('c1', 'h3', 1),
        ('o2', 'h4', 1),
    ])


def build_acetone_visual():
    return build_structure_visual([
        ('c1', 'C', 68, 150, 28),
        ('c2', 'C', 180, 150, 29),
        ('c3', 'C', 292, 150, 28),
        ('o', 'O', 180, 62, 27),
        ('h1', 'H', 24, 88, 20),
        ('h2', 'H', 18, 150, 20),
        ('h3', 'H', 24, 212, 20),
        ('h4', 'H', 336, 88, 20),
        ('h5', 'H', 342, 150, 20),
        ('h6', 'H', 336, 212, 20),
    ], [
        ('c1', 'c2', 1), ('c2', 'c3', 1), ('c2', 'o', 2),
        ('c1', 'h1', 1), ('c1', 'h2', 1), ('c1', 'h3', 1),
        ('c3', 'h4', 1), ('c3', 'h5', 1), ('c3', 'h6', 1),
    ])


def build_propane_visual():
    return build_structure_visual([
        ('c1', 'C', 70, 150, 27),
        ('c2', 'C', 180, 150, 27),
        ('c3', 'C', 290, 150, 27),
        ('h1', 'H', 28, 82, 19), ('h2', 'H', 18, 150, 19), ('h3', 'H', 28, 218, 19),
        ('h4', 'H', 180, 76, 19), ('h5', 'H', 180, 224, 19),
        ('h6', 'H', 332, 82, 19), ('h7', 'H', 342, 150, 19), ('h8', 'H', 332, 218, 19),
    ], [
        ('c1', 'c2', 1), ('c2', 'c3', 1),
        ('c1', 'h1', 1), ('c1', 'h2', 1), ('c1', 'h3', 1),
        ('c2', 'h4', 1), ('c2', 'h5', 1),
        ('c3', 'h6', 1), ('c3', 'h7', 1), ('c3', 'h8', 1),
    ])


def build_butane_visual():
    return build_structure_visual([
        ('c1', 'C', 45, 150, 24), ('c2', 'C', 135, 150, 24),
        ('c3', 'C', 225, 150, 24), ('c4', 'C', 315, 150, 24),
        ('h1', 'H', 16, 90, 17), ('h2', 'H', 12, 150, 17), ('h3', 'H', 16, 210, 17),
        ('h4', 'H', 135, 88, 17), ('h5', 'H', 135, 212, 17),
        ('h6', 'H', 225, 88, 17), ('h7', 'H', 225, 212, 17),
        ('h8', 'H', 344, 90, 17), ('h9', 'H', 348, 150, 17), ('h10', 'H', 344, 210, 17),
    ], [
        ('c1', 'c2', 1), ('c2', 'c3', 1), ('c3', 'c4', 1),
        ('c1', 'h1', 1), ('c1', 'h2', 1), ('c1', 'h3', 1),
        ('c2', 'h4', 1), ('c2', 'h5', 1),
        ('c3', 'h6', 1), ('c3', 'h7', 1),
        ('c4', 'h8', 1), ('c4', 'h9', 1), ('c4', 'h10', 1),
    ])


def build_ethylene_glycol_visual():
    return build_structure_visual([
        ('o1', 'O', 36, 150, 25), ('c1', 'C', 118, 150, 27),
        ('c2', 'C', 224, 150, 27), ('o2', 'O', 306, 150, 25),
        ('h1', 'H', 16, 98, 18), ('h2', 'H', 118, 78, 19), ('h3', 'H', 118, 222, 19),
        ('h4', 'H', 224, 78, 19), ('h5', 'H', 224, 222, 19), ('h6', 'H', 344, 150, 18),
    ], [
        ('h1', 'o1', 1), ('o1', 'c1', 1), ('c1', 'c2', 1), ('c2', 'o2', 1), ('o2', 'h6', 1),
        ('c1', 'h2', 1), ('c1', 'h3', 1), ('c2', 'h4', 1), ('c2', 'h5', 1),
    ])


def build_glycerol_visual():
    return build_structure_visual([
        ('c1', 'C', 80, 150, 25), ('c2', 'C', 180, 150, 25), ('c3', 'C', 280, 150, 25),
        ('o1', 'O', 80, 78, 23), ('o2', 'O', 180, 78, 23), ('o3', 'O', 280, 78, 23),
        ('h1', 'H', 42, 78, 17), ('h2', 'H', 142, 78, 17), ('h3', 'H', 318, 78, 17),
        ('h4', 'H', 80, 222, 18), ('h5', 'H', 180, 222, 18), ('h6', 'H', 280, 222, 18),
        ('h7', 'H', 34, 150, 18), ('h8', 'H', 326, 150, 18),
    ], [
        ('c1', 'c2', 1), ('c2', 'c3', 1),
        ('c1', 'o1', 1), ('c2', 'o2', 1), ('c3', 'o3', 1),
        ('o1', 'h1', 1), ('o2', 'h2', 1), ('o3', 'h3', 1),
        ('c1', 'h4', 1), ('c2', 'h5', 1), ('c3', 'h6', 1),
        ('c1', 'h7', 1), ('c3', 'h8', 1),
    ])


def build_diethyl_ether_visual():
    return build_structure_visual([
        ('c1', 'C', 38, 150, 22), ('c2', 'C', 108, 150, 24),
        ('o', 'O', 180, 150, 25), ('c3', 'C', 252, 150, 24), ('c4', 'C', 322, 150, 22),
        ('h1', 'H', 18, 92, 16), ('h2', 'H', 14, 150, 16), ('h3', 'H', 18, 208, 16),
        ('h4', 'H', 108, 92, 16), ('h5', 'H', 108, 208, 16),
        ('h6', 'H', 252, 92, 16), ('h7', 'H', 252, 208, 16),
        ('h8', 'H', 342, 92, 16), ('h9', 'H', 346, 150, 16), ('h10', 'H', 342, 208, 16),
    ], [
        ('c1', 'c2', 1), ('c2', 'o', 1), ('o', 'c3', 1), ('c3', 'c4', 1),
        ('c1', 'h1', 1), ('c1', 'h2', 1), ('c1', 'h3', 1),
        ('c2', 'h4', 1), ('c2', 'h5', 1),
        ('c3', 'h6', 1), ('c3', 'h7', 1),
        ('c4', 'h8', 1), ('c4', 'h9', 1), ('c4', 'h10', 1),
    ])


def ring_points(center_x, center_y, radius, count=6):
    return [
        (
            round(center_x + radius * math.cos((2 * math.pi * index / count) - math.pi / 6)),
            round(center_y + radius * math.sin((2 * math.pi * index / count) - math.pi / 6)),
        )
        for index in range(count)
    ]


def build_benzene_visual():
    points = ring_points(180, 150, 76)
    atoms = [(f'c{i}', 'C', x, y, 23) for i, (x, y) in enumerate(points)]
    hydrogens = []
    bonds = []

    for index, (x, y) in enumerate(points):
        bonds.append((f'c{index}', f'c{(index + 1) % 6}', 2 if index % 2 == 0 else 1))
        hx = round(180 + (x - 180) * 1.45)
        hy = round(150 + (y - 150) * 1.45)
        hydrogens.append((f'h{index}', 'H', hx, hy, 16))
        bonds.append((f'c{index}', f'h{index}', 1))

    return build_structure_visual(atoms + hydrogens, bonds)


def build_toluene_visual():
    visual = build_benzene_visual()
    c_ring = visual['nodes'][0]
    methyl = molecule_node('C', 320, c_ring['y'], 22)
    h1 = molecule_node('H', 344, c_ring['y'] - 44, 15)
    h2 = molecule_node('H', 350, c_ring['y'], 15)
    h3 = molecule_node('H', 344, c_ring['y'] + 44, 15)
    visual['nodes'].extend([methyl, h1, h2, h3])
    visual['bonds'].extend(
        molecule_bonds(c_ring, methyl)
        + molecule_bonds(methyl, h1)
        + molecule_bonds(methyl, h2)
        + molecule_bonds(methyl, h3)
    )
    return visual


def build_naphthalene_visual():
    atoms = [
        ('c1', 'C', 86, 150, 20), ('c2', 'C', 121, 88, 20), ('c3', 'C', 191, 88, 20),
        ('c4', 'C', 226, 150, 20), ('c5', 'C', 191, 212, 20), ('c6', 'C', 121, 212, 20),
        ('c7', 'C', 261, 88, 20), ('c8', 'C', 331, 88, 20), ('c9', 'C', 331, 212, 20), ('c10', 'C', 261, 212, 20),
    ]
    bonds = [
        ('c1', 'c2', 1), ('c2', 'c3', 2), ('c3', 'c4', 1), ('c4', 'c5', 2),
        ('c5', 'c6', 1), ('c6', 'c1', 2), ('c4', 'c7', 1), ('c7', 'c8', 2),
        ('c8', 'c9', 1), ('c9', 'c10', 2), ('c10', 'c5', 1),
    ]
    return build_structure_visual(atoms, bonds)


def build_glucose_visual():
    atoms = [
        ('o_ring', 'O', 180, 70, 20),
        ('c1', 'C', 258, 108, 20), ('c2', 'C', 258, 192, 20), ('c3', 'C', 180, 230, 20),
        ('c4', 'C', 102, 192, 20), ('c5', 'C', 102, 108, 20), ('c6', 'C', 38, 108, 18),
        ('o1', 'O', 318, 108, 18), ('o2', 'O', 318, 192, 18), ('o3', 'O', 180, 282, 18),
        ('o4', 'O', 42, 192, 18), ('o5', 'O', 38, 54, 18),
    ]
    bonds = [
        ('o_ring', 'c1', 1), ('c1', 'c2', 1), ('c2', 'c3', 1), ('c3', 'c4', 1),
        ('c4', 'c5', 1), ('c5', 'o_ring', 1), ('c5', 'c6', 1),
        ('c1', 'o1', 1), ('c2', 'o2', 1), ('c3', 'o3', 1), ('c4', 'o4', 1), ('c6', 'o5', 1),
    ]
    return build_structure_visual(atoms, bonds)


def build_sucrose_visual():
    first = build_glucose_visual()
    second_atoms = [
        molecule_node('O', 246, 150, 18), molecule_node('C', 292, 92, 17),
        molecule_node('C', 330, 132, 17), molecule_node('C', 315, 198, 17),
        molecule_node('C', 252, 210, 17),
    ]
    first['nodes'].extend(second_atoms)
    for start, end in zip(second_atoms, second_atoms[1:] + second_atoms[:1]):
        first['bonds'].extend(molecule_bonds(start, end))
    first['bonds'].extend(molecule_bonds(first['nodes'][1], second_atoms[0]))
    return first


def build_caffeine_visual():
    atoms = [
        ('n1', 'N', 94, 116, 20), ('c2', 'C', 154, 80, 20), ('n3', 'N', 222, 104, 20),
        ('c4', 'C', 236, 176, 20), ('c5', 'C', 174, 224, 20), ('c6', 'C', 106, 188, 20),
        ('o1', 'O', 156, 28, 17), ('o2', 'O', 302, 190, 17),
        ('n4', 'N', 174, 150, 18), ('c_m1', 'C', 48, 80, 16), ('c_m2', 'C', 270, 62, 16), ('c_m3', 'C', 166, 274, 16),
    ]
    bonds = [
        ('n1', 'c2', 1), ('c2', 'n3', 1), ('n3', 'c4', 1), ('c4', 'c5', 1),
        ('c5', 'c6', 2), ('c6', 'n1', 1), ('c2', 'o1', 2), ('c4', 'o2', 2),
        ('n1', 'c_m1', 1), ('n3', 'c_m2', 1), ('c5', 'c_m3', 1), ('n4', 'c2', 1), ('n4', 'c5', 1),
    ]
    return build_structure_visual(atoms, bonds)


def build_aspirin_visual():
    visual = build_benzene_visual()
    c0 = visual['nodes'][0]
    c3 = visual['nodes'][3]
    carbox_c = molecule_node('C', 320, c0['y'], 18)
    o1 = molecule_node('O', 346, c0['y'] - 42, 16)
    o2 = molecule_node('O', 346, c0['y'] + 42, 16)
    acet_o = molecule_node('O', 38, c3['y'], 16)
    acet_c = molecule_node('C', 18, c3['y'] + 50, 16)
    visual['nodes'].extend([carbox_c, o1, o2, acet_o, acet_c])
    visual['bonds'].extend(
        molecule_bonds(c0, carbox_c)
        + molecule_bonds(carbox_c, o1, 2)
        + molecule_bonds(carbox_c, o2)
        + molecule_bonds(c3, acet_o)
        + molecule_bonds(acet_o, acet_c)
    )
    return visual


def build_citric_acid_visual():
    atoms = [
        ('c1', 'C', 70, 150, 20), ('c2', 'C', 150, 150, 22), ('c3', 'C', 230, 150, 20),
        ('co1', 'C', 36, 88, 17), ('co2', 'C', 150, 68, 17), ('co3', 'C', 324, 150, 17),
        ('o1', 'O', 18, 44, 15), ('o2', 'O', 76, 54, 15),
        ('o3', 'O', 116, 28, 15), ('o4', 'O', 186, 28, 15),
        ('o5', 'O', 342, 104, 15), ('o6', 'O', 342, 196, 15),
        ('oh', 'O', 150, 230, 16),
    ]
    bonds = [
        ('c1', 'c2', 1), ('c2', 'c3', 1), ('c1', 'co1', 1), ('c2', 'co2', 1), ('c3', 'co3', 1),
        ('co1', 'o1', 2), ('co1', 'o2', 1), ('co2', 'o3', 2), ('co2', 'o4', 1), ('co3', 'o5', 2), ('co3', 'o6', 1),
        ('c2', 'oh', 1),
    ]
    return build_structure_visual(atoms, bonds)


CUSTOM_MOLECULE_BUILDERS = {
    'CH4': build_methane_visual,
    'CO2': build_carbon_dioxide_visual,
    'NH3': build_ammonia_visual,
    'H2O2': build_hydrogen_peroxide_visual,
    'C2H2': build_acetylene_visual,
    'C2H4': build_ethylene_visual,
    'C2H6': build_ethane_visual,
    'CH3OH': build_methanol_visual,
    'C2H5OH': build_ethanol_visual,
    'CH3COOH': build_acetic_acid_visual,
    'CH3COCH3': build_acetone_visual,
    'C3H8': build_propane_visual,
    'C4H10': build_butane_visual,
    'C2H4(OH)2': build_ethylene_glycol_visual,
    'C3H8O3': build_glycerol_visual,
    'C2H5OC2H5': build_diethyl_ether_visual,
    'C6H6': build_benzene_visual,
    'C7H8': build_toluene_visual,
    'C10H8': build_naphthalene_visual,
    'C6H12O6': build_glucose_visual,
    'C12H22O11': build_sucrose_visual,
    'C8H10N4O2': build_caffeine_visual,
    'C9H8O4': build_aspirin_visual,
    'C6H8O7': build_citric_acid_visual,
}


def build_molecule_visual(items):
    atoms = []
    total_count = sum(item['count'] for item in items)

    for item in items:
        repeat = item['count'] if total_count <= 14 else 1
        for index in range(repeat):
            atoms.append({
                'symbol': item['symbol'],
                'name': item['name'],
                'count': '' if total_count <= 14 else item['count'],
                'color': element_color(item['symbol']),
                'key': f"{item['symbol']}-{index}",
            })

    if not atoms:
        return {'nodes': [], 'bonds': []}

    center_index = next(
        (index for index, atom in enumerate(atoms) if atom['symbol'] != 'H'),
        0,
    )
    center_atom = atoms.pop(center_index)
    center_atom.update({'x': 180, 'y': 150, 'r': 38})
    center_atom.update({
        'badge_x': center_atom['x'] + center_atom['r'] - 6,
        'badge_y': center_atom['y'] + center_atom['r'] - 6,
    })

    nodes = [center_atom]
    bonds = []
    radius_x = 106
    radius_y = 76

    if len(atoms) == 1:
        center_atom.update({'x': 112, 'y': 150})
        center_atom.update({
            'badge_x': center_atom['x'] + center_atom['r'] - 6,
            'badge_y': center_atom['y'] + center_atom['r'] - 6,
        })

    single_atom_position = {'x': 248, 'y': 150}
    two_atom_positions = [
        {'x': 74, 'y': 150},
        {'x': 286, 'y': 150},
    ]
    cardinal_positions = [
        {'x': 180, 'y': 64},
        {'x': 286, 'y': 150},
        {'x': 180, 'y': 236},
        {'x': 74, 'y': 150},
        {'x': 92, 'y': 82},
        {'x': 268, 'y': 82},
        {'x': 268, 'y': 218},
        {'x': 92, 'y': 218},
    ]

    for index, atom in enumerate(atoms):
        if len(atoms) == 1:
            position = single_atom_position
        elif len(atoms) == 2:
            position = two_atom_positions[index]
        elif index < len(cardinal_positions):
            position = cardinal_positions[index]
        else:
            angle = (2 * math.pi * index / len(atoms)) - (math.pi / 2)
            position = {
                'x': round(180 + radius_x * math.cos(angle)),
                'y': round(150 + radius_y * math.sin(angle)),
            }

        atom.update({
            'x': position['x'],
            'y': position['y'],
            'r': 28,
        })
        atom.update({
            'badge_x': atom['x'] + atom['r'] - 6,
            'badge_y': atom['y'] + atom['r'] - 6,
        })
        bonds.append({
            'x1': center_atom['x'],
            'y1': center_atom['y'],
            'x2': atom['x'],
            'y2': atom['y'],
        })
        nodes.append(atom)

    return {'nodes': nodes, 'bonds': bonds}


def home(request):
    return render(request, 'home.html')


def about(request):
    return render(request, 'about.html')


def result(request):
    query = request.GET.get('query', '').strip()

    compound = None
    element = None
    related_elements = []
    risk_level = 1
    risk_class = 'risk-low'
    risk_percent = 0
    latex_formula = ''
    molecule_visual = {'nodes': [], 'bonds': []}
    message = ''

    if query:
        compound = (
            Compound.objects
            .filter(Q(formula__iexact=query) | Q(name__icontains=query))
            .first()
        )

        if not compound:
            element = (
                Element.objects
                .filter(Q(symbol__iexact=query) | Q(name__icontains=query))
                .first()
            )

        if not compound and not element:
            message = '검색 결과가 없습니다.'
    else:
        message = '화합물명, 화학식, 원소명 또는 원소 기호를 입력해주세요.'

    if compound:
        compound_elements = list(
            compound.compoundelement_set
            .select_related('element')
            .order_by('element__atomic_number')
        )
        related_elements = [item.element for item in compound_elements]
        risk_level = max(1, min(compound.risk_level, 5))
        risk_class = 'risk-low' if risk_level <= 1 else 'risk-mid' if risk_level <= 3 else 'risk-high'
        risk_percent = risk_level * 20
        latex_formula = formula_to_latex(compound.formula)
        custom_builder = CUSTOM_MOLECULE_BUILDERS.get(compound.formula.upper())
        if custom_builder:
            molecule_visual = custom_builder()
        else:
            molecule_visual = build_molecule_visual([
                {
                    'symbol': item.element.symbol,
                    'name': item.element.name,
                    'count': item.element_count,
                }
                for item in compound_elements
            ])
    elif element:
        latex_formula = formula_to_latex(element.symbol)
        molecule_visual = build_molecule_visual([{
            'symbol': element.symbol,
            'name': element.name,
            'count': 1,
        }])

    return render(request, 'result.html', {
        'query': query,
        'compound': compound,
        'element': element,
        'related_elements': related_elements,
        'risk_level': risk_level,
        'risk_class': risk_class,
        'risk_percent': risk_percent,
        'latex_formula': latex_formula,
        'molecule_visual': molecule_visual,
        'message': message,
    })
