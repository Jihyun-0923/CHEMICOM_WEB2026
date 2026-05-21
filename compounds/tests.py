from django.test import SimpleTestCase

from .views import (
    CUSTOM_MOLECULE_BUILDERS,
    build_acetylene_visual,
    build_ethanol_visual,
    build_molecule_visual,
    formula_to_latex,
)


class FormulaToLatexTests(SimpleTestCase):
    def test_converts_simple_formula_numbers_to_subscripts(self):
        self.assertEqual(
            formula_to_latex('C2H5OH'),
            r'\mathrm{C}_{2}\mathrm{H}_{5}\mathrm{O}\mathrm{H}',
        )

    def test_converts_parenthesized_formula_numbers_to_subscripts(self):
        self.assertEqual(
            formula_to_latex('Ca(OH)2'),
            r'\mathrm{Ca}(\mathrm{O}\mathrm{H})_{2}',
        )


class MoleculeVisualTests(SimpleTestCase):
    def test_expands_small_molecules_into_atom_nodes(self):
        visual = build_molecule_visual([
            {'symbol': 'H', 'name': '수소', 'count': 2},
            {'symbol': 'O', 'name': '산소', 'count': 1},
        ])

        self.assertEqual(len(visual['nodes']), 3)
        self.assertEqual(len(visual['bonds']), 2)
        self.assertEqual(visual['nodes'][0]['symbol'], 'O')
        self.assertEqual(visual['nodes'][1]['y'], visual['nodes'][2]['y'])

    def test_places_two_atom_molecules_horizontally(self):
        visual = build_molecule_visual([
            {'symbol': 'Na', 'name': '나트륨', 'count': 1},
            {'symbol': 'Cl', 'name': '염소', 'count': 1},
        ])

        self.assertEqual(len(visual['nodes']), 2)
        self.assertEqual(visual['nodes'][0]['y'], visual['nodes'][1]['y'])
        self.assertLess(visual['nodes'][0]['x'], visual['nodes'][1]['x'])

    def test_places_many_neighbors_in_cardinal_directions_first(self):
        visual = build_molecule_visual([
            {'symbol': 'C', 'name': '탄소', 'count': 1},
            {'symbol': 'H', 'name': '수소', 'count': 4},
        ])
        center, top, right, bottom, left = visual['nodes']

        self.assertEqual(top['x'], center['x'])
        self.assertLess(top['y'], center['y'])
        self.assertGreater(right['x'], center['x'])
        self.assertEqual(right['y'], center['y'])
        self.assertEqual(bottom['x'], center['x'])
        self.assertGreater(bottom['y'], center['y'])
        self.assertLess(left['x'], center['x'])
        self.assertEqual(left['y'], center['y'])

    def test_ethanol_visual_uses_structural_layout(self):
        visual = build_ethanol_visual()
        symbols = [node['symbol'] for node in visual['nodes']]
        c1, c2, o, h1, h2, h3, h4, h5, h6 = visual['nodes']

        self.assertEqual(symbols.count('C'), 2)
        self.assertEqual(symbols.count('O'), 1)
        self.assertEqual(symbols.count('H'), 6)
        self.assertEqual(len(visual['bonds']), 8)
        self.assertEqual(h1['x'], c1['x'])
        self.assertLess(h1['y'], c1['y'])
        self.assertLess(h2['x'], c1['x'])
        self.assertEqual(h2['y'], c1['y'])
        self.assertEqual(h3['x'], c1['x'])
        self.assertGreater(h3['y'], c1['y'])

    def test_all_custom_molecule_visuals_have_nodes_and_bonds(self):
        for formula, builder in CUSTOM_MOLECULE_BUILDERS.items():
            with self.subTest(formula=formula):
                visual = builder()
                self.assertGreater(len(visual['nodes']), 0)
                self.assertGreater(len(visual['bonds']), 0)

    def test_acetylene_visual_has_three_distinct_carbon_bonds(self):
        visual = build_acetylene_visual()
        carbon_bonds = [
            bond for bond in visual['bonds']
            if bond['x1'] == 122 and bond['x2'] == 238
        ]

        self.assertEqual(len(carbon_bonds), 3)
        self.assertEqual(
            sorted(bond['y1'] for bond in carbon_bonds),
            [140, 150, 160],
        )
