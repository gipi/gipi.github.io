# REGRESSIONI
#  1. chdir on texrender come back on error
#  2. rmdir tmpdir
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.comments.models import Comment
from django.utils.hashcompat import sha_constructor
from django.contrib.contenttypes.models import ContentType

from trackback.models import Trackback

from yadb.models import Blog
from yadb.utils import slugify

import os, glob, time, random

class RenderingTest(TestCase):
    fixtures = ['auth_data.json']
    def _preview(self, content):
        """
        Checks that calling the preview view, with argument content by
        a POST call, it return a 200 status code.

        Returns the response object.
        """
        self.client.login(username='test', password='password')
        response = self.client.post('/preview/',
            {'content': content},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        return response

    def test_directive_tex(self):
        content = r"""
        .. latex:: F_{\mu\nu} = \partial_\mu A_\nu - \partial_\nu A_\mu

        """
        self._preview(content)

    def test_directive_video(self):
        content = r"""
        .. video:: http://www.example.com

        """
        response = self._preview(content)
        self.assertNotContains(response, 'ERROR')

    def test_directive_tex_errors(self):
        content = r"""
        .. latex:: F_{\mu\nu} = \artial_\mu A_\nu - \partial_\nu A_\mu

        """
        response = self._preview(content)
        self.assertContains(response, 'ERROR')

    def test_role_tex(self):
        content = r"""
        lorem ipsum dixit :tex:`\alpha`,
        """
        self._preview(content)

    def test_role_tex_errors(self):
        content = r"""
        check if there is an error doesn't crash :tex:`\doesnotexist`
        """
        response = self._preview(content)
        self.assertContains(response, 'ERROR')

class BlogTests(TestCase):
    fixtures = [
        'site.json',
        'auth_data.json',
        'blog-data.json',
        'trackback.json',
    ]
    def test_blog_view_a_post(self):
        post = Blog.objects.get(pk=1)
        response = self.client.get(post.get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def test_page_and_comment_rendering(self):
        url = reverse('blog-post', args=['superfici-minimali-e-bolle-di-sapone',])
        response = self.client.get(url)

        # this checks :tex: role in comment doesn't work
        self.assertContains(response, 'ERROR', 2)

    def test_blog_add(self):
        # the page exists
        self.client.login(username='test', password='password')
        response = self.client.get(reverse('blog-add'))
        self.assertEqual(response.status_code, 200)

        previous_n = len(Blog.objects.all())

        # some errors
        response = self.client.post(reverse('blog-add'), {
            'content': 'this is a content',
            'tags': 'love, lulz' }
        )
        self.assertFormError(response, 'form', 'title',
                [u'This field is required.'])
        #self.assertRedirects(response, '/blog/')

        # can I submit without error
        response = self.client.post(reverse('blog-add'),
                {
                'title': 'This is a test',
                'content': 'this is a content',
                'tags': 'love, lulz',
                'status': 'pubblicato',
                })
        #self.assertRedirects(response, '/blog/')
        self.assertEqual(len(Blog.objects.all()), previous_n + 1)

    def test_blog_add_with_same_title(self):
        self.client.login(username='test', password='password')
        response = self.client.post(reverse('blog-add'),
                {
                'title': 'superfici minimali e bolle di sapone',
                'content': 'this is a content',
                'tags': 'love, lulz',
                'status': 'pubblicato',
                })
        self.assertFormError(response, 'form',
                'title', [u'Blog with this Title already exists.'])

    def test_blog_add_with_same_slug(self):
        self.client.login(username='test', password='password')
        initial_title = 'superfici-minimali-e-bolle-di-sapone'
        response = self.client.post(reverse('blog-add'),
                {
                'title': 'superfici minimali,e bolle di sapone',
                'content': 'this is a content',
                'tags': 'love, lulz',
                'status': 'pubblicato',
                })
        self.assertRedirects(response, '/blog/')
        self.assertEqual(initial_title + '-1',
        Blog.objects.get(title='superfici minimali,e bolle di sapone').slug)

    def test_edit(self):
        pk = 2
        url = reverse('blog-edit', args=[pk])
        self.client.login(username='test', password='password')

        self.assertEqual(Blog.objects.get(pk=pk).status, 'bozza')

        previous_n = len(Blog.objects.all())

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        blog = response.context[0]['form'].instance

        self.assertEqual(blog.status, 'bozza')

        previous_date = blog.creation_date

        post_data = {
            'title': blog.title,
            'content': blog.content,
            'tags': blog.tags,
            # change only this
            'status': 'pubblicato',
        }
        response = self.client.post(url, post_data)

        # if the forms has not errors then redirects
        self.assertEqual(response.context, None)
        self.assertRedirects(response, '/blog/')

        self.assertEqual(len(Blog.objects.all()), previous_n)

        blog = Blog.objects.get(pk=pk)
        # check that published date is now
        self.assertEqual(previous_date < blog.creation_date, True)

    def test_trackback(self):
        # OUT
        self.client.login(username='test', password='password')
        response = self.client.post(reverse('blog-add'), {
            'title': 'This is a test',
            'content': r"""
            this a test for external trackback http://testserver/blog/post/superfici-minimali-e-bolle-di-sapone/
            """,
            'tags': 'love, lulz',
            'status': 'pubblicato',
        })
        #self.assertContains(response, 'OK')

        # IN pingback (take a random post)
        all_posts = Blog.objects.all()
        length = len(all_posts)
        instance = random.choice(all_posts)
        url_to_pingback = 'http://testserver%s' % instance.get_absolute_url()

        response = self.client.post(reverse('receive_pingback'),
        """<?xml version="1.0"?>
        <methodCall>
        <methodName>pingback.ping</methodName>
        <params>
               <param>
                       <value>
                               <string>http://www.example.com</string>
                       </value>
               </param>
               <param>
                       <value>
                               <string>%s</string>
                       </value>
               </param>
        </params>
        </methodCall>
        """ % url_to_pingback, content_type='application/xml')

        self.assertContains(response, 'OK')
        pingback = Trackback.objects.all()
        self.assertEqual(pingback[len(pingback) - 1].content_object, instance)

        # IN trackback
        content_type = ContentType.objects.get(model='blog', app_label='yadb')
        response = self.client.post(
                reverse('receive_trackback',
                    args=[content_type.pk, instance.pk]),
            {
                'title': 'an awesome trackback',
                'excerpt': 'did it for the lulz',
                'url': 'http://www.example.com'
            })
        self.assertContains(response, '<error>0</error>')

    def test_blog_list_with_bozza(self):
        url = reverse('blog-list')
        response = self.client.get(url)
        self.assertEqual(len(response.context[0]['blogs']), 1)

    def test_blog_view_bozza_when_logged(self):
        url = reverse('blog-list')

        # first check there are only published
        response = self.client.get(url)
        self.assertEqual(len(response.context[0]['blogs']), 1)

        # second check for unpublished when you are logged
        self.client.login(username='test', password='password')
        response = self.client.get(url)
        self.assertEqual(len(response.context[0]['blogs']), 2)

    def test_blog_order(self):
        self.client.login(username='test', password='password')
        url = reverse('blog-list')
        response = self.client.get(url)
        blogs = response.context[0]['blogs']
        self.assertEqual(blogs[0].creation_date > blogs[1].creation_date, True)

    def _get_uploaded_file_name(self):
        return settings.UPLOAD_PATH + os.path.basename(__file__)

    def _upload_my_self(self):
        url = reverse('blog-upload')

        # then open THIS file
        filez = open(__file__, 'r')

        post_data = {
            'file': filez,
        }
        response = self.client.post(url, post_data)
        filez.close()

        uploaded_file = self._get_uploaded_file_name()
        self.assertEqual(os.stat(uploaded_file) != None, True)

        return response

    def test_upload(self):
        # first delete previously 'tests.py.<digit>' files
        uploaded_file = self._get_uploaded_file_name()
        for file in  glob.iglob(uploaded_file + '*'):
            os.remove(file)

        #   1. the file is being uploaded
        self.client.login(username='test', password='password')

        response = self._upload_my_self()
        self.assertRedirects(response, reverse('blog-list'))

        #   2. if a file has the same name of one yet uploaded add a number
        response = self._upload_my_self()
        self.assertRedirects(response, reverse('blog-list'))

        uploaded_file = self._get_uploaded_file_name()
        self.assertEqual(os.stat(uploaded_file + '.1') != None, True)

        self._upload_my_self()
        self.assertEqual(os.stat(uploaded_file + '.2') != None, True)

    def test_archives(self):
        url = reverse('blog-archives')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context[0]['blogs']), 1)

        self.client.login(username='test', password='password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context[0]['blogs']), 2)

    def _generate_post_data_for_comment(self, pk, text):
        """Generate a (SHA1) security hash from the provided info.
           copyied from django.contrib.comment.forms
        """
        content_type = 'yadb.blog'
        object_pk = str(pk)
        timestamp = str(int(time.time()))
        info = (content_type, object_pk, timestamp, settings.SECRET_KEY)
        security_hash = sha_constructor("".join(info)).hexdigest()

        return {
            'name': 'gianluca',
            'email': 'gianluca.pacchiella@ktln2.org',
            'url': 'http://ktln2.org',
            'comment': text,
            # security stuffs
            'content_type': content_type,
            'object_pk': object_pk,
            'timestamp': timestamp,
            'security_hash': security_hash,
        }

    def test_comment_moderation(self):
        n_before = len(Comment.objects.all())
        url = '/comments/post/'
        post_data = self._generate_post_data_for_comment(1,
                'yeah, it\'s internet baby!!!')
        response = self.client.post(url, post_data)
        self.assertRedirects(response, '/comments/posted/?c=%d' % (n_before + 1))

        n_after =  len(Comment.objects.all())
        self.assertEqual(n_after == (n_before + 1), True)

        #from django.core import mail
        #self.assertEqual(len(mail.outbox), 1)

    def test_sidebar(self):
        url = reverse('blog-list')
        response = self.client.get(url)
        self.assertContains(response, '<div id="sidebar">')
class AuthTest(TestCase):
    fixtures = ['auth_data.json']
    def test_login(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('login'),
                {'username': 'test', 'password': 'password'})
        self.assertRedirects(response, reverse('home'), target_status_code=301)

    def test_logout(self):
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 200)

    def test_blog_add(self):
        response = self.client.get(reverse('blog-add'))
        self.assertRedirects(response,
                '/login/?next=' + reverse('blog-add'))

    def test_upload(self):
        response = self.client.get(reverse('blog-upload'))
        self.assertRedirects(response,
                '/login/?next=' + reverse('blog-upload'))

    def test_preview(self):
        # in order to preview need to login
        response = self.client.get('/preview/')
        self.assertRedirects(response, '/login/?next=/preview/')

        response = self.client.post('/preview/', {'content': 'miao'})
        self.assertRedirects(response, '/login/?next=/preview/')

        # need XMLHttpRequest
        self.client.login(username='test', password='password')
        response = self.client.get('/preview/')
        self.assertEqual(response.status_code, 400)

        response = self.client.post('/preview/',
                {'content': 'miao'})
        self.assertEqual(response.status_code, 400)

        # so we use it
        response = self.client.post('/preview/',
                {'content': 'miao'},
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

class UtilTests(TestCase):
    def test_slugify(self):
        slug = slugify('l\'amore non ESISTE')
        self.assertEqual(slug, 'l-amore-non-esiste')

        slug = slugify('here there aren\'t two  dashes or     more')
        self.assertEqual(slug, 'here-there-aren-t-two-dashes-or-more')

        slug = slugify('here there aren\'t # @ ^')
        self.assertEqual(slug, 'here-there-aren-t')


class FeedsTests(TestCase):
    fixtures = ['auth_data.json', 'blog-data.json',]
    def test_existence(self):
        response = self.client.get('/feeds/latest/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yadb/feeds_title.html')
        self.assertTemplateUsed(response, 'yadb/feeds_description.html')

        # check for user realated feeds
        response = self.client.get('/feeds/user/test/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Blog object')

        # TODO: check for a precise number of posts

class MainSiteTests(TestCase):
    urls = 'static_urls'
    def test_favicon(self):
        response = self.client.get('/favicon.ico')
        print response
        self.assertRedirects(response,
                '/media/images/favicon.ico', status_code=301)

    def test_robots(self):
        response = self.client.get('/robots.txt')
        print response
        self.assertRedirects(response,
                '/media/robots.txt', status_code=301)

# TODO: move to a file with general tests
class AboutTests(TestCase):
    fixtures = [settings.PROJECT_ROOT + '/fixtures/initial_data.yaml']
    def test_page_exists(self):
        url = '/about/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
