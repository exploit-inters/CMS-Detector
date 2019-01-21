import asyncio
from json import load
from urllib.parse import urlsplit

from aiofiles import open as afile
from aiohttp import ClientSession, ClientTimeout


async def save(where, what):
    async with afile(f'{where}.txt', 'a',
                     encoding="utf-8",
                     errors="ignore") as f:
        await f.write(f'{what}\n')


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

    if not await alive(url):
        return

    for item in cms:
        try:
            temp = await item[0](url)

            if temp[0]:
                await save(item[1], temp[1])
                break
        except:
            pass


async def main():
    count = 0
    tasks = []

    async with afile('links', errors='ignore', encoding='utf-8') as links:
        async for link in links:
            task = asyncio.ensure_future(
                purgatory(
                    link.strip()
                )
            )
            tasks.append(task)

            count += 1
            print(f'Passed: {count}', end='\r')

            if len(tasks) >= settings['threads']:
                await asyncio.gather(*tasks)
                tasks = []

    if len(tasks) != 0:
        await asyncio.gather(*tasks)
        tasks = []


if __name__ == "__main__":
    settings = load(open('settings.json', 'r'))

    _dle = [dle, 'dle']
    _bitrix = [bitrix, 'bitrix']
    _joomla = [joomla, 'joomla']
    _drupal = [drupal, 'drupal']
    _magento = [magento, 'magento']
    _wordpress = [wordpress, 'wordpress']

    cms = [_dle, _bitrix, _joomla, _drupal, _magento, _wordpress]
    timeout = ClientTimeout(total=settings['timeout'])

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
