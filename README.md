# AI agent `rednote`
 AI agent for www.xiaohongshu.com thread

![](https://shields.io/badge/dependencies-Python_3.12-blue)
![](https://shields.io/badge/dependencies-Azure_OpenAI_Service-blue)


## Acknowledgement

[xhshow](https://github.com/Cloxl/xhshow) (modified)

## Install

Make sure you have a [rednote](https://www.xiaohongshu.com) social media account.

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

Deploy a GPT model that supports [function calling](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/function-calling) in [Azure OpenAI Service](https://learn.microsoft.com/en-us/azure/ai-services/openai/), for example `gpt-4o`.

Create a JSON file `config.json` in the program's root directory. Fill in API key, API version (in format of [date](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes) string `%Y-%m-%d`), endpoint (in format of `https://*.openai.azure.com/`), model type (e.g. `gpt-4o`), and deployment name. The schema is shown as follows.

```json
{
  "azure_api_key": "",
  "azure_api_version": "",
  "azure_endpoint": "",
  "azure_model_type": "",
  "azure_deployment_name": ""
}
```

## Usage

Run the following command.

```
python app.py
```

When the program hints that `rednote` cookies are expired: 

- Visit `rednote` and log in your account
- Export cookies by J2TEAMS extension (a file will be downloaded)
- Upload the file in this program's hint page

*You can replace cookies (therefore can switch between `rednote` accounts) by click "replace cookies" at left-bottom corner of main page. Existed conversations will not be affected by replacing cookies. Therefore, the conversations, which is created long time ago, cannot continue visiting data fetching tools.*

