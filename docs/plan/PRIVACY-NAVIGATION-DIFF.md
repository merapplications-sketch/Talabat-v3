# Privacy text — proposed addition for navigation and tracking (NOT applied)

**Where the live text is.** The customer app shows «Конфиденциальность / Privacy» from the database table `app_pages`, row
`slug = 'privacy'`, fields `body_ru` / `body_en` (patch 25: every signed-in user reads it; only the admin function `set_page()`
changes it, from the admin panel). The repository does not contain the live wording, so the exact current text must be read first:

```sql
-- read-only
select slug, body_ru, body_en from app_pages where slug = 'privacy';
```

The addition below is appended to the end of the current text by the owner (admin panel → pages → «privacy»), after review.
Nothing is changed automatically. Wording facts are from the provider's published policy (Geoapify privacy policy, 25 Oct 2026).

## RU — добавить в конец
**Маршруты и отслеживание доставки.**
Когда во время доставки включена встроенная навигация, сервер TALABOT отправляет сервису маршрутов Geoapify (geoapify.com)
только две точки: текущее местоположение курьера и точку назначения (ресторан или отмеченную клиентом точку доставки). Имя,
телефон, номер заказа и другие данные аккаунта не передаются. Запрос отправляет сервер TALABOT, а не телефон клиента или курьера.
По опубликованной политике Geoapify данные успешных запросов хранятся у провайдера не более 24 часов и используются для
контроля доступа и учёта использования; серверы провайдера находятся в ЕС.
Если курьер сам выбирает внешнее приложение (Яндекс Карты, 2ГИС или Google Maps), это приложение получает точку назначения
и обрабатывает её по своей политике.
Пока заказ в пути, клиент этого заказа видит последнее местоположение курьера и время его обновления; после доставки или
отмены оно больше не показывается.

## EN — append at the end
**Routes and delivery tracking.**
When in-app navigation is on during a delivery, the TALABOT server sends the routing service Geoapify (geoapify.com) only
two points: the courier's current position and the destination (the restaurant or the delivery point marked by the customer).
No name, phone, order number or other account data is sent. The request is made by the TALABOT server, not by the customer's or
courier's phone. Under Geoapify's published policy, data of successful requests is kept by the provider for no longer than
24 hours and is used for access control and usage counting; the provider's servers are in the EU.
If the courier chooses an external app (Yandex Maps, 2GIS or Google Maps), that app receives the destination point and
handles it under its own policy.
While an order is on the way, the customer of that order sees the courier's last position and when it was updated; after
delivery or cancellation it is no longer shown.

## Checks before publishing the text
- Confirm the in-app wording matches the activation state (if internal navigation stays off, the first paragraph can wait).
- The courier-tracking paragraph applies already (patch 39 is live).
- Source: https://geoapify.com/privacy-policy (request body, headers, IP, timestamp retained; successful requests ≤ 24 h; EU hosting).
