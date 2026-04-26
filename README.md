# MCP: "rednote" assistant
MCP server which collects data from www.xiaohongshu.com social media

![](https://shields.io/badge/dependencies-Python_3.13-blue)
[![](https://shields.io/badge/dependencies-rednote-BE0000)](https://www.xiaohongshu.com/explore)
![](https://shields.io/badge/OS-Windows_≥_10-lightgrey)


## Acknowledgement

[xhshow](https://github.com/Cloxl/xhshow)



## Install

### Cookies extraction tool

If you have [Chromium-based browsers](https://en.wikipedia.org/wiki/Chromium_(web_browser)#Browsers_based_on_Chromium), please install [J2TEAM cookies](https://chromewebstore.google.com/detail/j2team-cookies/okpidcojinmlaakglciglbpcpajaibco) extension. Otherwise, you need to find an alternative extension to export, or manually copy cookies to local file.

>   [!NOTE]
>
>   If you don't use Chromium-based browsers or prefer another way to extract the cookies (alternative extension or manual process), the format of extracted cookies file is defined in JSON schema `cookies_schema.json`.
>
>   [JSON schema editor](https://github.com/cloudy-sfu/JSON-schema-editor) can check whether the extracted cookies file (instance) fits `cookies_schema.json` (template).

### Python program

Confirm you have a [rednote](www.xiaohongshu.com) account.

Visit https://www.xiaohongshu.com and log in your "rednote" account.

Export the cookies with J2TEAMS Cookies or alternatives to file `$xiaohongshu_cookies_path`.

Create and a Python 3.13 virtual environment and activate. Run the following command.

```
pip install -r requirements.txt
python cookies.py --input_path $xiaohongshu_cookies_path
```

Save the output before closing, because the output is MCP configuration information.

### Update cookies

If MCP server fails to start, extract the new cookies to file `$xiaohongshu_cookies_path`. 

Go to this program's folder, activate Python virtual environment.

Run the following command.

```
python cookies.py --input_path $xiaohongshu_cookies_path
```



### MCP config

Let the root folder of this program be `$base_dir`.

MCP configuration:

| Item    | Value                      |
| ------- | -------------------------- |
| Name    | rednote-agent              |
| Type    | stdio                      |
| Command | $base_dir/start_server.ps1 |



### Update version

Update source code of this MCP server.

Update cookies. Turn off and on this MCP server again.

