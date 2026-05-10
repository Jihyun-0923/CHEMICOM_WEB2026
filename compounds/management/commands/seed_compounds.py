from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = '원소 및 화합물 초기 데이터를 생성합니다.'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING(
                '아직 입력할 초기 데이터가 없습니다. 데이터 담당자가 자료를 전달하면 이 명령을 채워주세요.'
            )
        )
