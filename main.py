# -*- coding: utf-8 -*-

import asyncio
import contextlib
from json import loads
from ssl import SSLError
from urllib.parse import urlsplit

from aiofiles import open as afile
from aiohttp import ClientSession, ClientTimeout


@contextlib.contextmanager
def silent_out():
    loop = asyncio.get_event_loop()
    old_handler = loop.get_exception_handler()
    old_handler_fn = old_handler

    def ignore_exc(_loop, ctx):
        exc = ctx.get('exception')

        if isinstance(exc, SSLError):
            return

        old_handler_fn(loop, ctx)

    loop.set_exception_handler(ignore_exc)

    try:
        yield
    finally:
        loop.set_exception_handler(old_handler)


async def joomla(url):
    try:
        async with ClientSession(timeout=timeout) as s:
            async with s.get(url+'/administrator', ssl=False) as r:
                txt = await r.text()

                assert r.status == 200
                assert 'content="Joomla' in txt
                assert 'name="USER_PASSWORD"' in txt

                l = urlsplit(str(r.url))
                url = f'{l.scheme}://{l.netloc}/bitrix/admin/?login=yes'

                return [True, url]
    except:
        return [False, '']


async def bitrix(url):
    try:
        async with ClientSession(timeout=timeout) as s:
            async with s.get(url+'/bitrix/admin', ssl=False) as r:
                txt = await r.text()

                assert r.status == 200
                assert '/bitrix/admin/?login=yes' in txt

                return [True, str(r.url)]
    except:
        return [False, '']


async def dle(url):
    try:
        async with ClientSession(timeout=timeout) as s:
            async with s.get(url + '/admin.php') as r:
                txt = await r.text()

                assert 'dle_act_lang' in txt or 'value="dologin"' in txt
                assert 'selected_language' in txt

                return [True, str(r.url)]
    except:
        return [False, '']


async def wordpress(url):
    try:
        async with ClientSession(timeout=timeout) as session:
            r = await session.get(url + '/wp-login.php')

            assert 'id="wp-submit"' in await r.text()

            return [True, str(r.url)]
    except:
        return [False, '']


async def magento(url):
    try:
        async with ClientSession(timeout=timeout) as s:
            async with s.get(url + '/admin') as r:
                txt = await r.text()

                assert 'id="login" name="login[password]"' in txt

                return [True, str(r.url)]
    except:
        return [False, '']


async def drupal(url):
    try:
        async with ClientSession(timeout=timeout) as s:
            async with s.get(url + '/admin') as r:
                txt = await r.text()

                try:
                    assert r.status == 403 and 'Drupal' in txt
                except:
                    b = r.history[0].status
                    c = r.history[0].headers['Location']

                    if b == 301:
                        b = r.history[1].status
                        c = r.history[1].headers['Location']

                    assert b == 302 and 'user/login?destination=admin' in c

                l = urlsplit(str(r.url))
                l = f'{l.scheme}://{l.netloc}/user/login?destination=admin'

                return [True, l]
    except:
        return [False, '']


async def save(where, what):
    async with afile(f'{where}.txt', 'a',
                     encoding="utf-8",
                     errors="ignore") as f:
        await f.write(f'{what}\n')


async def alive(url):
    try:
        async with ClientSession(timeout=timeout) as s:
            async with s.get(url) as r:
                if r.status == 200:
                    return True
                else:
                    return False
    except:
        return False


async def purgatory(url):
    url = url if 'http' in url else 'http://' + url

    with silent_out():
        if await alive(url) is False:
            return

        for item in cms:
            temp = await item[0](url)

            if temp[0]:
                await save(item[1], temp[1])
                break


async def main():
    count = 0
    tasks = []

    async with afile('links', errors='ignore', encoding='utf-8') as links:
        async for link in links:
            count += 1
            task = asyncio.create_task(
                purgatory(
                    link.strip('\n')
                )
            )
            tasks.append(task)

            print(f'Passed: {count}', end='\r')

            if len(tasks) >= settings['threads']:
                await asyncio.gather(*tasks)
                tasks = []

    if len(tasks) != 0:
        await asyncio.gather(*tasks)
        tasks = []


if __name__ == "__main__":

    settings = loads(open('settings.json', 'r').read())

    _dle = [dle, 'dle']
    _bitrix = [bitrix, 'bitrix']
    _joomla = [joomla, 'joomla']
    _drupal = [drupal, 'drupal']
    _magento = [magento, 'magento']
    _wordpress = [wordpress, 'wordpress']

    cms = [_dle, _bitrix, _joomla, _drupal, _magento, _wordpress]
    timeout = ClientTimeout(total=settings['timeout'])

    asyncio.run(main())
