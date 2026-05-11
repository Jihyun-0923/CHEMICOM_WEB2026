import re
import zipfile
from collections import Counter
from decimal import Decimal
from pathlib import Path
from xml.etree import ElementTree

from django.conf import settings
from django.core.management.base import CommandError, BaseCommand
from django.db import transaction

from compounds.models import Compound, CompoundElement, Element


XLSX_FILE = 'Chemical_Database_for_Beginners.xlsx'
XML_NS = {
    'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
    'rel': 'http://schemas.openxmlformats.org/package/2006/relationships',
    'officeRel': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
}

ACID_BASE_MAP = {
    'acid': Compound.AcidBaseType.ACID,
    'base': Compound.AcidBaseType.BASE,
    'neutral': Compound.AcidBaseType.NEUTRAL,
    'amphoteric': Compound.AcidBaseType.AMPHOTERIC,
    'unknown': Compound.AcidBaseType.UNKNOWN,
}

FALLBACK_ELEMENTS = {
    'Ba': {
        'name': '바륨',
        'atomic_number': 56,
        'weight': Decimal('137.327'),
        'description': '화합물 분자식 연결을 위해 자동 보완된 원소',
    },
    'Cr': {
        'name': '크롬',
        'atomic_number': 24,
        'weight': Decimal('51.996'),
        'description': '화합물 분자식 연결을 위해 자동 보완된 원소',
    },
    'Mn': {
        'name': '망가니즈',
        'atomic_number': 25,
        'weight': Decimal('54.938'),
        'description': '화합물 분자식 연결을 위해 자동 보완된 원소',
    },
    'Pb': {
        'name': '납',
        'atomic_number': 82,
        'weight': Decimal('207.200'),
        'description': '화합물 분자식 연결을 위해 자동 보완된 원소',
    },
    'Zn': {
        'name': '아연',
        'atomic_number': 30,
        'weight': Decimal('65.380'),
        'description': '화합물 분자식 연결을 위해 자동 보완된 원소',
    },
}


def parse_decimal(value):
    return Decimal(str(value)).quantize(Decimal('0.001'))


def column_index(cell_ref):
    letters = re.match(r'[A-Z]+', cell_ref).group(0)
    index = 0
    for letter in letters:
        index = index * 26 + ord(letter) - ord('A') + 1
    return index - 1


def shared_strings(xlsx):
    try:
        root = ElementTree.fromstring(xlsx.read('xl/sharedStrings.xml'))
    except KeyError:
        return []

    strings = []
    for item in root.findall('main:si', XML_NS):
        parts = [
            text.text or ''
            for text in item.findall('.//main:t', XML_NS)
        ]
        strings.append(''.join(parts))
    return strings


def workbook_sheets(xlsx):
    workbook = ElementTree.fromstring(xlsx.read('xl/workbook.xml'))
    rels = ElementTree.fromstring(xlsx.read('xl/_rels/workbook.xml.rels'))
    rel_targets = {
        rel.attrib['Id']: rel.attrib['Target']
        for rel in rels.findall('rel:Relationship', XML_NS)
    }

    sheets = {}
    for sheet in workbook.findall('main:sheets/main:sheet', XML_NS):
        rel_id = sheet.attrib[
            '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
        ]
        target = rel_targets[rel_id]
        if not target.startswith('xl/'):
            target = f'xl/{target}'
        sheets[sheet.attrib['name']] = target
    return sheets


def cell_value(cell, strings):
    value_type = cell.attrib.get('t')

    if value_type == 'inlineStr':
        return ''.join(
            text.text or ''
            for text in cell.findall('.//main:t', XML_NS)
        )

    value = cell.find('main:v', XML_NS)
    if value is None:
        return ''

    raw = value.text or ''
    if value_type == 's':
        return strings[int(raw)]
    if value_type == 'b':
        return raw == '1'
    if re.fullmatch(r'-?\d+', raw):
        return int(raw)
    if re.fullmatch(r'-?\d+(\.\d+)?', raw):
        return Decimal(raw)
    return raw


def read_sheet(xlsx_path, sheet_name):
    with zipfile.ZipFile(xlsx_path) as xlsx:
        strings = shared_strings(xlsx)
        sheets = workbook_sheets(xlsx)
        if sheet_name not in sheets:
            raise CommandError(f'{sheet_name} 시트를 찾을 수 없습니다.')

        root = ElementTree.fromstring(xlsx.read(sheets[sheet_name]))
        rows = []
        for row in root.findall('main:sheetData/main:row', XML_NS):
            values = []
            for cell in row.findall('main:c', XML_NS):
                index = column_index(cell.attrib['r'])
                while len(values) <= index:
                    values.append('')
                values[index] = cell_value(cell, strings)
            rows.append(values)
        return rows


def rows_as_dicts(rows):
    headers = [str(header).strip() for header in rows[0]]
    for row in rows[1:]:
        if not any(value != '' for value in row):
            continue
        yield {
            headers[index]: row[index] if index < len(row) else ''
            for index in range(len(headers))
        }


def parse_formula(formula):
    tokens = re.findall(r'[A-Z][a-z]?|\d+|[()]', formula)
    if ''.join(tokens) != formula:
        raise CommandError(f'지원하지 않는 분자식 형식입니다: {formula}')

    stack = [Counter()]
    index = 0
    while index < len(tokens):
        token = tokens[index]

        if token == '(':
            stack.append(Counter())
            index += 1
            continue

        if token == ')':
            if len(stack) == 1:
                raise CommandError(f'괄호가 맞지 않는 분자식입니다: {formula}')
            group = stack.pop()
            index += 1
            multiplier = 1
            if index < len(tokens) and tokens[index].isdigit():
                multiplier = int(tokens[index])
                index += 1
            for symbol, count in group.items():
                stack[-1][symbol] += count * multiplier
            continue

        if re.fullmatch(r'[A-Z][a-z]?', token):
            symbol = token
            index += 1
            count = 1
            if index < len(tokens) and tokens[index].isdigit():
                count = int(tokens[index])
                index += 1
            stack[-1][symbol] += count
            continue

        raise CommandError(f'지원하지 않는 분자식 형식입니다: {formula}')

    if len(stack) != 1:
        raise CommandError(f'괄호가 맞지 않는 분자식입니다: {formula}')

    return stack[0]


class Command(BaseCommand):
    help = '엑셀 파일의 원소와 화합물 데이터를 DB에 반영합니다.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            default=str(settings.BASE_DIR / XLSX_FILE),
            help='가져올 xlsx 파일 경로',
        )

    def handle(self, *args, **options):
        xlsx_path = Path(options['file'])
        if not xlsx_path.exists():
            raise CommandError(f'엑셀 파일을 찾을 수 없습니다: {xlsx_path}')

        element_rows = list(rows_as_dicts(read_sheet(xlsx_path, 'Element')))
        compound_rows = list(rows_as_dicts(read_sheet(xlsx_path, 'Compound')))

        element_counts = {'created': 0, 'updated': 0}
        compound_counts = {'created': 0, 'updated': 0}
        relation_count = 0

        with transaction.atomic():
            for row in element_rows:
                _, created = Element.objects.update_or_create(
                    atomic_number=int(row['atomic_number']),
                    defaults={
                        'name': str(row['name']).strip(),
                        'weight': parse_decimal(row['weight']),
                        'description': str(row['description']).strip(),
                        'symbol': str(row['symbol']).strip(),
                    },
                )
                element_counts['created' if created else 'updated'] += 1

            all_symbols = set(Element.objects.values_list('symbol', flat=True))
            needed_symbols = set()
            for row in compound_rows:
                needed_symbols.update(parse_formula(str(row['formula']).strip()))

            for symbol in sorted(needed_symbols - all_symbols):
                if symbol not in FALLBACK_ELEMENTS:
                    raise CommandError(f'{symbol} 원소 정보가 없어 관계를 만들 수 없습니다.')

                defaults = FALLBACK_ELEMENTS[symbol]
                _, created = Element.objects.update_or_create(
                    symbol=symbol,
                    defaults=defaults,
                )
                element_counts['created' if created else 'updated'] += 1

            elements_by_symbol = {
                element.symbol: element
                for element in Element.objects.all()
            }

            for row in compound_rows:
                formula = str(row['formula']).strip()
                acid_base_type = ACID_BASE_MAP.get(
                    str(row['acid_base_type']).strip().lower(),
                    Compound.AcidBaseType.UNKNOWN,
                )

                compound, created = Compound.objects.update_or_create(
                    formula=formula,
                    defaults={
                        'name': str(row['name']).strip(),
                        'weight': parse_decimal(row['weight']),
                        'description': str(row['description']).strip(),
                        'acid_base_type': acid_base_type,
                        'usage': str(row['usage']).strip(),
                        'caution': str(row['caution']).strip(),
                        'risk_level': int(row['risk_level']),
                    },
                )
                compound_counts['created' if created else 'updated'] += 1

                CompoundElement.objects.filter(compound=compound).delete()
                for symbol, count in parse_formula(formula).items():
                    CompoundElement.objects.create(
                        compound=compound,
                        element=elements_by_symbol[symbol],
                        element_count=count,
                    )
                    relation_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                'DB 반영 완료: '
                f"원소 {element_counts['created']}개 생성/{element_counts['updated']}개 갱신, "
                f"화합물 {compound_counts['created']}개 생성/{compound_counts['updated']}개 갱신, "
                f'화합물-원소 관계 {relation_count}개 생성'
            )
        )
