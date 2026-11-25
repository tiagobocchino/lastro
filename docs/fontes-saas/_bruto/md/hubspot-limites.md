> ## Documentation Index
> Fetch the complete documentation index at: https://developers.hubspot.com/docs/llms.txt
> Use this file to discover all available pages before exploring further.

---
id: 6458e7ea-6deb-44b1-8730-bde1b6ebb3b6
---

# API usage guidelines and limits

> Learn about the different API and developer feature limits in HubSpot.

HubSpot closely monitors usage of all APIs to ensure a quality experience for every user. All app and integration developers must comply with the [HubSpot Acceptable Use Policy](https://legal.hubspot.com/acceptable-use) and [API Terms](https://legal.hubspot.com/hs-developer-terms). While HubSpot reserves the right to change or deprecate the APIs over time, updates will always be provided in advance through the [Developer Changelog](https://developers.hubspot.com/changelog).

[Super Admins](https://knowledge.hubspot.com/user-management/hubspot-user-permissions-guide#super-admin) can review [API call usage](https://knowledge.hubspot.com/account-management/review-account-limits).

## Authentication and security

For optimal security, all apps must use HubSpot’s [OAuth protocol](https://developers.hubspot.com/docs/apps/developer-platform/build-apps/authentication/overview.md#oauth) directly, or use your app's static auth token if you're building an [app installed in a single account](https://developers.hubspot.com/docs/apps/developer-platform/build-apps/app-configuration.md#distribution). Apps are responsible for storing time-to-live (TTL) data and refreshing user access tokens in accordance with this protocol. When an access token is generated, it will include an `expires_in` parameter indicating how long it can be used to make API calls before refreshing. `Unauthorized (401)` requests are not a valid indicator that a new access token must be retrieved.

## Checking API usage

### Apps built on version 2025.2 and 2026.03 of the developer platform

To view API usage for your apps built on the [new developer platform](https://developers.hubspot.com/docs/apps/developer-platform/overview.md):

1. In your HubSpot account, navigate to **Development** in the main navigation bar.
2. In the left sidebar menu, navigate to **Monitoring** > **API call usage**.
3. Your API usage across all your apps will be listed at the top of the page. You can also review usage for the apps you built in your specific account, along with any third-party apps you've installed.

### Legacy apps

**To view API usage for a legacy [private app](https://developers.hubspot.com/docs/apps/legacy-apps/private-apps/overview.md):**

1. In your HubSpot account, navigate to **Development** in the main navigation bar.
2. In the left sidebar menu, navigate to **Legacy apps**.
3. Click the **name** of the private app.
4. On the app details page, click the **Logs** tab.
5. Review the API calls listed in the table. You can also use the **search bar**, **filters**, and **date pickers** to further refine the displayed API calls.

**Learn more about [checking API usage in legacy private apps](https://developers.hubspot.com/docs/apps/legacy-apps/private-apps/overview.md).**

To view API usage for a public app using OAuth:

1. In your HubSpot account, navigate to **Development** in the main navigation bar.
2. In the left sidebar menu, navigate to **Monitoring**, then select **Logs**.
3. At the top, select the **name** of the app.
4. Use the **tabs** to view different types of requests being made to or from the app. While viewing these logs, you can click an **individual request** to view more information.

Learn more about [monitoring API usage for legacy public apps](https://developers.hubspot.com/docs/apps/legacy-apps/public-apps/overview.md#monitor-app-behavior).

## Rate limits

The number of calls your app can make is based on your account subscription in the account it's installed in, and whether you've purchased the [API limit increase](https://legal.hubspot.com/hubspot-product-and-services-catalog#Addons).

You can keep the following general limits in mind when making requests to HubSpot's API endpoints, however some APIs may also have more specific limits listed on their relevant API guide (e.g., the [exports API](https://developers.hubspot.com/docs/api-reference/latest/crm/exports/guide.md#limits)).

> [!WARNING]
>
> The following APIs have limits that are unique from or stricter than the general limits. Refer to each associated guide for more information.
>
> * [Associations API](https://developers.hubspot.com/docs/api-reference/latest/crm/associations/associate-records/guide.md#limits)
> * [CRM Search API](https://developers.hubspot.com/docs/api-reference/latest/crm/search-the-crm.md#limits)
> * [GraphQL API](https://developers.hubspot.com/docs/cms/start-building/features/data-driven-content/graphql/query-hubspot-data-using-graphql.md#query-complexity-and-account-limits)

### Publicly distributed OAuth app limits

For [legacy public apps](https://developers.hubspot.com/docs/apps/legacy-apps/public-apps/overview.md), and apps on the latest versions of the developer platform (2025.2 and 2026.03) using [OAuth authentication](https://developers.hubspot.com/docs/apps/developer-platform/build-apps/authentication/overview.md#oauth) [distributed](https://developers.hubspot.com/docs/apps/developer-platform/build-apps/app-configuration.md#distribution) via the HubSpot marketplace, each HubSpot account that installs your app is limited to 110 requests every 10 seconds. This excludes the [CRM Search API](https://developers.hubspot.com/docs/api-reference/latest/crm/search-the-crm.md).

> [!WARNING]
>
> The [API limit increase add-on](https://legal.hubspot.com/hubspot-product-and-services-catalog#Addons) does not increase the limits of [legacy public apps](https://developers.hubspot.com/docs/apps/legacy-apps/public-apps/overview.md) nor apps on the latest versions of the developer platform (2025.2 and 2026.03) using [OAuth authentication](https://developers.hubspot.com/docs/apps/developer-platform/build-apps/authentication/overview.md#oauth) that are [distributed](https://developers.hubspot.com/docs/apps/developer-platform/build-apps/app-configuration.md#distribution) via the HubSpot marketplace.

### Privately distributed app limits

The limits in the table below apply to [legacy private apps](https://developers.hubspot.com/docs/apps/legacy-apps/private-apps/overview.md), as well as apps on the latest versions of the developer platform (2025.2 and 2026.03) with a [distribution](https://developers.hubspot.com/docs/apps/developer-platform/build-apps/app-configuration.md#distribution) set to `private`. Note that for these privately distributed app types:

* The burst limit, detailed in the *Per 10 seconds* column below, applies individually per app.
* The daily limit, detailed in the *Per day* column below, is shared across all apps within the same HubSpot account.

| | **Product Tier** | **Per 10 Seconds** | **Per Day** |
| - | - | - | - |
| Privately distributed apps | (Any Hub)  Free and Starter | 100 / app | 250,000 / account |
| | (Any Hub)  Professional | 190 / app | 625,000 / account |
| | (Any Hub)  Enterprise | 190 / app | 1,000,000 / account |
| Privately distributed apps with [API Limit Increase](https://legal.hubspot.com/hubspot-product-and-services-catalog#Addons) | (Any Hub)  Free, Starter, Professional, and Enterprise | 250 / app | 1,000,000 / account on top of your base subscription, for each limit increase. You can purchase a maximum of two API limit increases. |

### Exemptions

Some APIs are exempt from the 10-second and daily limits (e.g., certain [marketing single send API](https://developers.hubspot.com/docs/api-reference/latest/marketing/transactional-emails/guide.md) and [source code API](https://developers.hubspot.com/docs/api-reference/latest/cms/source-code/guide.md) endpoints). However, you should note the following for the exempt APIs:

* API requests that are exempt from daily or secondary limits will not be logged in HubSpot. If you want to store these exempted requests, you'll need to log these requests externally.
* A high number of requests may result in `5xx` errors. These can be addressed the same as you would [`429` errors](#rate-limit-error-responses).

## App and account limits

The following limits apply for creating legacy apps, webhook subscriptions, and CRM extension settings.

* You can create up to 100 [legacy public apps](https://developers.hubspot.com/docs/apps/legacy-apps/public-apps/overview.md) per developer account.
* You can create up to 20 [legacy private apps](https://developers.hubspot.com/docs/apps/legacy-apps/private-apps/overview.md) per HubSpot account.
* You can create up to 1,000 [webhook subscriptions](https://developers.hubspot.com/docs/api-reference/latest/webhooks) per app.
* You can create up to 25 CRM extension settings per [legacy public app](https://developers.hubspot.com/docs/apps/legacy-apps/public-apps/overview.md).

## API-specific limits

Some features and APIs have more limits that are listed below. Additional limis for each API can also be found on an API's associated guide (e.g., the [exports API](https://developers.hubspot.com/docs/api-reference/latest/crm/exports/guide.md#limits)).

### Timeline event limits

[Timeline events](https://developers.hubspot.com/docs/api-reference/legacy/crm/extensions/timeline/guide.md) in a legacy public app are subject to the following limits:

* You can create up to 750 timeline event types per public app.
* You can create up to 500 properties per timeline event type.
* Each serialized event instance has the following size limits:
  * 500 bytes for the event instance ID
  * 510 KB per property/token
  * 1 MB in total size for the event instance

### Custom event limits

[Custom events](https://developers.hubspot.com/docs/api-reference/latest/events/send-event-data/guide.md) are subject to the following limits:

* There is a limit of 500 unique event definitions per account.
* There is a limit of 30 million event completions per month.
* The send custom event completions endpoint supports up to 1250 requests per second.
* The custom event completion batch endpoint supports batches of 500.

Consult the other custom event restrictions in the [API guide](https://developers.hubspot.com/docs/api-reference/latest/events/send-event-data/guide.md#limits).

## Service limits

Learn more about service limits and pricing on [HubSpot's Product & Services Catalog](https://legal.hubspot.com/hubspot-product-and-services-catalog).

## Rate limit error responses

Any app or integration exceeding its rate limits will receive a `429` error response for all subsequent API calls. Requests resulting in an error response shouldn’t exceed 5% of your total daily requests. If you plan on listing your app in the [HubSpot Marketplace](https://ecosystem.hubspot.com/marketplace/apps), it must stay under this 5% limit to be certified.

The `429` response will have the following format:

```json theme={null}
{
  "status": "error",
  "message": "You have reached your daily limit.",
  "errorType": "RATE_LIMIT",
  "correlationId": "c033cdaa-2c40-4a64-ae48-b4cec88dad24",
  "policyName": "DAILY",
  "requestId": "3d3e35b7-0dae-4b9f-a6e3-9c230cbcf8dd"
}
```

The `message` and `policyName` will indicate which limit you hit (either daily or secondly).

The **daily** limit resets at midnight based on your [time zone setting](https://knowledge.hubspot.com/account-management/change-your-language-and-region-settings).

The following table details the rate limit headers included in the response of each API request to HubSpot, subject to the exceptions listed below the table.

| **Header** | **Description** |
| - | - |
| `X-HubSpot-RateLimit-Daily` | The number of API requests that are allowed per day. Note that this header is not included in the response to API requests authorized using [OAuth](https://developers.hubspot.com/docs/apps/developer-platform/build-apps/authentication/oauth/working-with-oauth.md). |
| `X-HubSpot-RateLimit-Daily-Remaining` | The number of API requests still allowed for the current day. Note that this header is not included in the response to API requests authorized using [OAuth](https://developers.hubspot.com/docs/apps/developer-platform/build-apps/authentication/oauth/working-with-oauth.md). |
| `X-HubSpot-RateLimit-Interval-Milliseconds` | The window of time that the `X-HubSpot-RateLimit-Max` and `X-HubSpot-RateLimit-Remaining` headers apply to.For example, a value of 10000 would be a window of 10 seconds. |
| `X-HubSpot-RateLimit-Max` | The number of requests allowed in the window specified in `X-HubSpot-RateLimit-Interval-Milliseconds`.For example, if this header had a value of 100, and the `X-HubSpot-RateLimit-Interval-Milliseconds` header was 10000, the enforced limit would be 100 requests per 10 seconds. |
| `X-HubSpot-RateLimit-Remaining` | The number of API requests still allowed for the window specified in `X-HubSpot-RateLimit-Interval-Milliseconds`. |

> [!WARNING]
>
> * The `X-HubSpot-RateLimit-Secondly` and `X-HubSpot-RateLimit-Secondly-Remaining` headers are still included and will still have accurate data, but the limit referenced by these headers is no longer enforced and these two headers should be considered deprecated.
> * Responses from the search API endpoints will not include any of the rate limit headers listed above.

You can also check the number of calls used during the current day using [this endpoint](https://developers.hubspot.com/docs/api-reference/latest/account/account-information/guide.md).

## Address rate limit issues

The sections below detail two possible ways you can reduce the volume of API traffic if you repeatedly hit your API request limit. If you're running into the `TEN_SECONDLY_ROLLING` limit, you should throttle the requests that your app is making to stay under that limit. In addition to throttling the requests, or if you're running into the daily limit, check out the suggestions below.

If you find that you're still hitting the call limits after looking through these suggestions, please post on HubSpot's [developer forums](https://community.hubspot.com/c/hubspot-developer-support/58). You should include as many details as possible about the APIs you're using, how you're using them, and which limit you're hitting.

### Use batch APIs and cache results when possible

If your site or app uses data from HubSpot on each page load, that data should be cached and loaded from that cache instead of being requested from the HubSpot APIs each time. If you're making repeated calls to get settings from your account for a batch job (such as getting your object properties, owners, or settings for a form), those settings should also be cached when possible.

### Use webhooks to get updated data from HubSpot

If you have a HubSpot Marketing Enterprise subscription, you can use webhook actions in workflows to have data for contact records sent to your system. Webhooks can be triggered as an action in any workflow, so you can use any workflow [starting conditions](https://knowledge.hubspot.com/workflows/understand-workflow-object-types) as the criteria to have contact data sent to your system. More details about using webhooks can be found [here](https://knowledge.hubspot.com/workflows/how-do-i-use-webhooks-with-hubspot-workflows) and example webhooks data is [here](https://developers.hubspot.com/docs/api-reference/legacy/automation/workflows/guide.md). Webhook calls made via workflows do not count towards the API rate limit.
