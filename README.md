# Date me please
Этот проект представляет собой API сервиса для поиска своей второй половинки.
Разрабатывался в качестве тестового задания.


## Как пользоваться API
Система предоставляет два способа тестирования API:

1. Встроенная панель Django REST Framework с самоописывающим API.
2. Подключенный для более удобного и привычного многим тестирования Swagger. 

Чтобы воспользоваться первым вариантом, просто сделайте GET-запрос на нужный вам эндпоинт.
Чтобы воспользоваться вторым вариантом, вы можете сделать GET-запрос по шаблонному пути ```/api/doc```.

> СОВЕТ:
> Используйте Swagger для ознакомления с API и его структурой, а панель DRF - для непосредственного тестирования.

## Описание API
Здесь вы сможете подробнее узнать о функционале сервиса.

### Доступ к API
Некоторые эндпоинты защищены от неавторизованных пользователей. Чтобы получить к ним доступ, создайте пользователя и авторизируйтесь.

> СОВЕТ:
> Перед использованием API создайте и авторизируйте пользователя. Для авторизации следует нажать на кнопку Session Login в Swagger'e или на кнопку Log In в панеле DRF. Кнопка Authorize в Swagger'e не работает.

### Регистрация пользователей
При использовании Swagger'a для регистрации пользователю понадобится указать его гендер, аватар, долготу и широту. Все эти данные указываются в поле ```profile```. Однако это неудобный способ, т.к. все данные придется записывать вручную в JSON-формате. Панель DRF предоставляет удобную форму для регистрации пользователей по адресу ```/api/clients/create```.

> СОВЕТ:
> Используйте панель DRF по адресу ```/api/clients/create``` для регистарции пользователей с помощью формы.

### Оценивание участников
Каждый участник может оценить другого участника по ```/api/clients/{id}/match```.
При этом оценивший участник попадает в так называемый "список влюбленных" участника, которого он оценил.
Каждый участник может проверить этот список по адресу ```/api/clients/me/lovers```.
Если пользователь оценит кого-то в ответ из этого списка, он получит об этом сообщение и почту человека, которого он оценил в ответ. При этом на почты участников отправятся письма о взаимной симпатии.

### Фильтрация списка пользователей
Список пользователей можно фильтровать по заданным параметрам.
Особое внимание стоит уделить параметру дистанции. В параметре ```distance_to_user``` указывается максимально допустимое расстояние от пользователя в километрах. Когда вы отправляете запрос ```/api/list/?distance_to_user={some_value}```, с помощью функций СУБД для каждого пользователя высчитывается расстояние на основе координат текущего пользователя и его самого. Дистанция пользователя с ним самим, разумеется, равна 0.0.

## Мысли разработчика
При разработке этого проекта по ТЗ разработчик был в некотором когнитивном диссонансе, однако решил не выдумывать и четко следовать ТЗ, оставив свои мысли здесь.
По мнению разработчика было бы уместно внести в ТЗ следующие корректировки:

1. Заменить маршрут ```/api/list``` на ```/api/clients``` с GET-запросом. Если есть необходимость в оптимизации расхода трафика, можно добавить маршрут ```/api/clients/list``` для получения не всех данных о пользователях, а только их юзернеймов.
2. По заветам REST API, лучше описывать API с помощью сущностей и методов запроса. Иными словами, стоит заменить ```/api/clients/create``` на ```/api/clients``` с POST-запросом.
3. Разделить приложение ```clients``` на два приложения: ```auth``` - для авторизации и регистрации пользователей, и, например, ```finder_lovers``` для поиска второй половинки.
4. Авторизация с помощью JWT-токенов добавлена на случай, если бы у сервиса был клиент, способный правильно работать с таким интерфейсом. Авторизация при тестировании работает с помощью обычных сессий, т.к. были проблемы настройки авторизации через токены в панелях Swagger'a и DRF. 
