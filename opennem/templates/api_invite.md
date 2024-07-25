Dear ${invite.name},

You have been invited to join the OpenNEM API.

Your API key is:

${invite.api_key}

Please keep this key safe. You can view the API docs at:

https://api.opennem.org.au/docs

and developer documentation at:

https://developers.opennem.org.au

You pass the API key as a Authorization Bearer token in the header of all requests.

Your API access level is: ${invite.access_level} and you have a limit of ${invite.limit} requests per ${invite.limit_interval}.

To check your API usage you can access the endpoint at:

https://api.opennem.org.au/v4/me

Example curl request:

curl -X GET -H "Content-Type:application/json" -H "Authorization: Bearer ${invite.api_key}" https://api.opennem.org.au/v4/me

If you would like to join the OpenNEM slack, click on the following invite link:

https://join.slack.com/t/opennem/shared_invite/zt-2n7g3fwaf-b0105_JXY~5cI6MZhbexzA

You can reply to this email to get support.

Kind regards,

The OpenNEM team
