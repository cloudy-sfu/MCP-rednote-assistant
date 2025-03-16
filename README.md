# AI agent `rednote`
 AI agent for www.xiaohongshu.com thread

![](https://shields.io/badge/dependencies-Python_3.12-blue)
![](https://shields.io/badge/OS-Windows_10_64--bit-navy)

## Acknowledgement

[xhshow](https://github.com/Cloxl/xhshow) (modified)

## Install

Create and activate a Python 3.12 virtual environment. Set the current directory to the program's root directory. Run the following command.

```
pip install -r requirements.txt
```

If you have [Chromium-based browsers](https://en.wikipedia.org/wiki/Chromium_(web_browser)#Browsers_based_on_Chromium), please install [J2TEAM cookies](https://chromewebstore.google.com/detail/j2team-cookies/okpidcojinmlaakglciglbpcpajaibco) extension. Otherwise, you need to find an alternative extension or manually copy any website's cookies from browser.

> [!NOTE]
>
> Function `auth.dump_cookies` is designed to load J2TEAM output files. If you use an alternative extension or manually paste the cookies, you need to modify this function, because pasted cookies table is in different format.
>
> The output table of `auth.dump_cookies` must have the following columns at least:
>
> - `name`
> - `value`
> - `expirationDate`  the expiry date of this cookies item
>
> Other columns are ignored.
>
> The output table must be saved in CSV format.



## Usage

To get the cookies file,

1. Visit https://www.xiaohongshu.com/explore and export the cookies by J2TEAM cookies.
2. Select this cookies file when the program requires.

