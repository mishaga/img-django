from django.core.management.base import BaseCommand, CommandError

from app.helpers import Size
from images.models import Image


class Command(BaseCommand):
    """Creates resizes for all images for user.

    Sample how to run: python manage.py create_resizes --width=700 --height=700 --username=test
    """

    def add_arguments(self, parser) -> None:
        """Add arguments."""
        parser.add_argument('--width', type=int)
        parser.add_argument('--height', type=int)
        parser.add_argument('--username', type=str)

    def handle(self, *args, **options) -> None:
        """Run the command."""
        if options['width'] < 1:
            raise CommandError('Width should be greater than 1')
        if options['height'] < 1:
            raise CommandError('Height should be greater than 1')

        cnt = 0
        size = Size(options['width'], options['height'])
        for image in Image.objects.filter(user__username=options['username']):
            image.resize(size)
            cnt += 1
            self.stdout.write('.', ending='')

        if cnt > 0:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS(f'Created {cnt} images'))
        else:
            self.stdout.write('Nothing to create')
