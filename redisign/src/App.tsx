import { useEffect, useState, type ReactNode } from "react"

type IconProps = {
  name: "search" | "sun" | "moon" | "arrow" | "github" | "telegram" | "rss" | "menu" | "close"
  size?: number
}

function Icon({ name, size = 18 }: IconProps) {
  const paths: Record<IconProps["name"], ReactNode> = {
    search: (
      <>
        <circle cx="11" cy="11" r="7" />
        <path d="m20 20-4-4" />
      </>
    ),
    sun: (
      <>
        <circle cx="12" cy="12" r="4" />
        <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
      </>
    ),
    moon: (
      <path d="M20.5 14.3A8.5 8.5 0 0 1 9.7 3.5 8.5 8.5 0 1 0 20.5 14.3Z" />
    ),
    arrow: (
      <>
        <path d="M5 12h14" />
        <path d="m14 7 5 5-5 5" />
      </>
    ),
    github: (
      <path d="M12 2.8a9.2 9.2 0 0 0-2.9 17.9c.5.1.6-.2.6-.5v-1.8c-2.8.6-3.4-1.2-3.4-1.2-.4-1.1-1.1-1.4-1.1-1.4-.9-.6.1-.6.1-.6 1 0 1.5 1 1.5 1 .9 1.5 2.3 1.1 2.9.8.1-.6.3-1.1.6-1.3-2.2-.3-4.5-1.1-4.5-4.6 0-1 .4-1.8 1-2.5-.1-.3-.4-1.2.1-2.5 0 0 .8-.3 2.6 1a9 9 0 0 1 4.8 0c1.8-1.2 2.6-1 2.6-1 .5 1.3.2 2.2.1 2.5.6.7 1 1.5 1 2.5 0 3.5-2.3 4.3-4.5 4.6.4.3.7.9.7 1.8v3.6c0 .3.2.6.7.5A9.2 9.2 0 0 0 12 2.8Z" />
    ),
    telegram: (
      <path d="m21 4-3 15.5c-.2 1-1 1.2-1.8.7l-4.6-3.4-2.2 2.1c-.2.2-.4.4-.9.4l.3-4.7 8.6-7.8c.4-.3-.1-.5-.6-.2L5.2 13.3.6 11.9c-1-.3-1-1 .2-1.5L19 3.4c.8-.3 1.6.2 2 .6Z" />
    ),
    rss: (
      <>
        <circle cx="5" cy="19" r="1.5" fill="currentColor" stroke="none" />
        <path d="M4 11a9 9 0 0 1 9 9M4 5a15 15 0 0 1 15 15" />
      </>
    ),
    menu: (
      <>
        <path d="M4 7h16M4 12h16M4 17h16" />
      </>
    ),
    close: (
      <>
        <path d="m6 6 12 12M18 6 6 18" />
      </>
    ),
  }

  return (
    <svg
      aria-hidden="true"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {paths[name]}
    </svg>
  )
}

function Logo() {
  return (
    <a className="logo" href="#" aria-label="Python.ru — на главную">
      <svg className="python-mark" viewBox="0 0 36 36" aria-hidden="true">
        <path
          fill="#3776ab"
          d="M17.8 2.5c-7.9 0-7.4 3.4-7.4 3.4v3.5H18v1H7.3S2.2 9.8 2.2 17.8s4.5 7.7 4.5 7.7h2.7v-3.8s-.1-4.5 4.4-4.5h7.5s4.2.1 4.2-4.1V6.4s.6-3.9-7.7-3.9Zm-4.2 2.4c.8 0 1.4.6 1.4 1.4s-.6 1.4-1.4 1.4-1.4-.6-1.4-1.4.6-1.4 1.4-1.4Z"
        />
        <path
          fill="#ffd343"
          d="M18.2 33.5c7.9 0 7.4-3.4 7.4-3.4v-3.5H18v-1h10.7s5.1.6 5.1-7.4-4.5-7.7-4.5-7.7h-2.7v3.8s.1 4.5-4.4 4.5h-7.5s-4.2-.1-4.2 4.1v6.7s-.6 3.9 7.7 3.9Zm4.2-2.4c-.8 0-1.4-.6-1.4-1.4s.6-1.4 1.4-1.4 1.4.6 1.4 1.4-.6 1.4-1.4 1.4Z"
        />
      </svg>
      <span>
        Python<span className="logo-dot">.</span>ru
      </span>
    </a>
  )
}

const articles = [
  {
    type: "СТАТЬЯ",
    tags: ["Python", "архитектура"],
    title: "Почему asyncio — это не потоки",
    description:
      "Разбираемся, что на самом деле происходит внутри event loop и где заканчивается магия асинхронности.",
    author: "Адриан Макриденко",
    date: "5 октября",
    time: "12 мин",
  },
  {
    type: "ПЕРЕВОД",
    tags: ["CPython"],
    title: "Что изменилось в Python 3.14: практический обзор",
    description:
      "Свободная многопоточность, новый интерпретатор и другие изменения, которые заметит разработчик.",
    author: "Анна Чернова",
    date: "3 октября",
    time: "9 мин",
  },
  {
    type: "СТАТЬЯ",
    tags: ["PostgreSQL", "backend"],
    title: "Очереди без брокера: опыт использования SKIP LOCKED",
    description:
      "Как упростить инфраструктуру небольшого сервиса и не пожалеть об этом через полгода.",
    author: "Илья Зверев",
    date: "30 сентября",
    time: "15 мин",
  },
]

const events = [
  {
    day: "07",
    month: "ОКТ",
    title: "ТехСреда: Python & Data",
    place: "Москва · Офлайн",
  },
  {
    day: "22",
    month: "ОКТ",
    title: "Moscow AI Meetup",
    place: "Москва · Офлайн",
  },
  {
    day: "14",
    month: "НОЯ",
    title: "Moscow Python №101",
    place: "Москва + Онлайн",
  },
  {
    day: "21",
    month: "НОЯ",
    title: "PiterPy Meetup",
    place: "Санкт-Петербург",
  },
]

const projects = [
  {
    name: "FastStream",
    description: "Фреймворк для работы с брокерами сообщений",
    stars: "4.2k",
    tag: "async",
  },
  {
    name: "Taskiq",
    description: "Распределённые очереди задач для Python",
    stars: "1.4k",
    tag: "backend",
  },
  {
    name: "Dishka",
    description: "Контейнер внедрения зависимостей",
    stars: "1.2k",
    tag: "tools",
  },
  {
    name: "Piccolo",
    description: "Быстрый async ORM и query builder",
    stars: "1.5k",
    tag: "database",
  },
]

function Meta({ children }: { children: ReactNode }) {
  return <div className="meta">{children}</div>
}

function SectionHeading({
  eyebrow,
  title,
  link,
}: {
  eyebrow?: string
  title: string
  link?: string
}) {
  return (
    <div className="section-heading">
      <div>
        {eyebrow && <span className="eyebrow">{eyebrow}</span>}
        <h2>{title}</h2>
      </div>
      {link && (
        <a className="arrow-link" href="#">
          {link}
          <Icon name="arrow" size={16} />
        </a>
      )}
    </div>
  )
}

function App() {
  const [dark, setDark] = useState(false)
  const [searchOpen, setSearchOpen] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)

  useEffect(() => {
    document.documentElement.dataset.theme = dark ? "dark" : "light"
  }, [dark])

  useEffect(() => {
    const close = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setSearchOpen(false)
        setMenuOpen(false)
      }
    }
    window.addEventListener("keydown", close)
    return () => window.removeEventListener("keydown", close)
  }, [])

  return (
    <div className="site-shell">
      <header className="site-header">
        <div className="container header-inner">
          <Logo />
          <nav
            className={`main-nav ${menuOpen ? "is-open" : ""}`}
            aria-label="Основная навигация"
          >
            <a href="#materials">Статьи</a>
            <a href="#notes">Заметки</a>
            <a href="#events">События</a>
            <a href="#community">Сообщество</a>
            <a href="#opensource">Open Source</a>
          </nav>
          <div className="header-actions">
            <button
              className="icon-button search-button"
              onClick={() => setSearchOpen(true)}
              aria-label="Открыть поиск"
            >
              <Icon name="search" />
              <span>Поиск</span>
              <kbd>⌘ K</kbd>
            </button>
            <button
              className="icon-button"
              onClick={() => setDark(!dark)}
              aria-label={
                dark ? "Включить светлую тему" : "Включить тёмную тему"
              }
            >
              <Icon name={dark ? "sun" : "moon"} />
            </button>
            <button
              className="icon-button mobile-menu"
              onClick={() => setMenuOpen(!menuOpen)}
              aria-label="Открыть меню"
            >
              <Icon name={menuOpen ? "close" : "menu"} />
            </button>
          </div>
        </div>
      </header>

      <main>
        <section className="intro container">
          <div>
            <span className="eyebrow">Основан в 1999 году</span>
            <h1>
              Русскоязычное
              <br />
              Python-сообщество.
            </h1>
          </div>
          <p>
            Люди, события и код вокруг Python.
            <br />
            Независимый портал, который делает само сообщество.
          </p>
        </section>

        <section className="container now-section">
          <SectionHeading eyebrow="Главное" title="Сейчас на Python.ru" />
          <div className="lead-grid">
            <article className="lead-story">
              <div className="story-index">01</div>
              <div className="lead-content">
                <div className="label-row">
                  <span className="content-label">ИНТЕРВЬЮ</span>
                  <span className="tag">open source</span>
                </div>
                <h2>
                  <a href="#">
                    «Open source держится не на коде, а на доверии»
                  </a>
                </h2>
                <p>
                  Никита Соболев — о поддержке популярных библиотек, выгорании
                  мейнтейнеров и о том, зачем российским разработчикам свои
                  проекты.
                </p>
                <Meta>
                  <span>Никита Соболев</span>
                  <span>6 октября</span>
                  <span>14 мин</span>
                </Meta>
              </div>
            </article>
            <div className="secondary-stories">
              <article>
                <span className="content-label note">ЗАМЕТКА</span>
                <h3>
                  <a href="#">PyPy опять рано хоронят</a>
                </h3>
                <p>
                  В свежей версии особенно интересны улучшения совместимости с
                  пакетами на C.
                </p>
                <Meta>
                  <span>Сегодня, 10:42</span>
                </Meta>
              </article>
              <article>
                <span className="content-label news">НОВОСТЬ</span>
                <h3>
                  <a href="#">Опубликован релиз Python 3.14</a>
                </h3>
                <p>Поддержка свободной многопоточности стала официальной.</p>
                <Meta>
                  <span>Вчера</span>
                  <span>3 мин</span>
                </Meta>
              </article>
            </div>
          </div>
        </section>

        <div className="container content-layout">
          <section id="materials" className="feed-section">
            <SectionHeading title="Свежие материалы" link="Все материалы" />
            <div className="article-list">
              {articles.map((article, index) => (
                <article className="article-row" key={article.title}>
                  <div className="article-number">
                    {String(index + 2).padStart(2, "0")}
                  </div>
                  <div>
                    <div className="label-row">
                      <span className="content-label">{article.type}</span>
                      {article.tags.map((tag) => (
                        <span className="tag" key={tag}>
                          {tag}
                        </span>
                      ))}
                    </div>
                    <h3>
                      <a href="#">{article.title}</a>
                    </h3>
                    <p>{article.description}</p>
                    <Meta>
                      <span>{article.author}</span>
                      <span>{article.date}</span>
                      <span>{article.time}</span>
                    </Meta>
                  </div>
                </article>
              ))}
            </div>
            <a className="text-button" href="#">
              Показать больше материалов <Icon name="arrow" size={17} />
            </a>
          </section>

          <aside className="sidebar">
            <section id="events" className="events-block">
              <SectionHeading eyebrow="Календарь" title="Ближайшие события" />
              <div className="event-list">
                {events.map((event) => (
                  <a className="event-row" href="#" key={event.title}>
                    <time>
                      <b>{event.day}</b>
                      <span>{event.month}</span>
                    </time>
                    <span>
                      <strong>{event.title}</strong>
                      <small>{event.place}</small>
                    </span>
                  </a>
                ))}
              </div>
              <a className="arrow-link" href="#">
                Все события <Icon name="arrow" size={16} />
              </a>
            </section>
            <section className="digest-block">
              <span className="eyebrow">Письмо раз в неделю</span>
              <h3>Дайджест Python.ru</h3>
              <p>Главные материалы, новости и события — без шума.</p>
              <form onSubmit={(e) => e.preventDefault()}>
                <input
                  type="email"
                  aria-label="Электронная почта"
                  placeholder="you@example.com"
                />
                <button type="submit">Подписаться</button>
              </form>
            </section>
          </aside>
        </div>

        <section id="notes" className="notes-section">
          <div className="container">
            <SectionHeading
              eyebrow="Короткий формат"
              title="Заметки сообщества"
              link="Все заметки"
            />
            <div className="notes-grid">
              <article>
                <span className="note-bracket">[1]</span>
                <p>
                  <a href="#">
                    В Python 3.14 появился новый тип интерпретатора. Собрали
                    первые бенчмарки — результаты не совсем те, что ожидали.
                  </a>
                </p>
                <Meta>
                  <span>Иван Ткачёв</span>
                  <span>1 час назад</span>
                </Meta>
              </article>
              <article>
                <span className="note-bracket">[2]</span>
                <p>
                  <a href="#">
                    Маленький трюк с <code>itertools.batched</code>, который
                    сделал код пайплайна заметно читаемее.
                  </a>
                </p>
                <Meta>
                  <span>Мария Коваль</span>
                  <span>Вчера</span>
                </Meta>
              </article>
              <article>
                <span className="note-bracket">[3]</span>
                <p>
                  <a href="#">
                    Ищем докладчиков на ноябрьский PiterPy. Можно приходить даже
                    с пятиминутной lightning talk.
                  </a>
                </p>
                <Meta>
                  <span>SPb Python</span>
                  <span>2 дня назад</span>
                </Meta>
              </article>
            </div>
          </div>
        </section>

        <section id="opensource" className="container open-source-section">
          <SectionHeading
            eyebrow="Сделано здесь"
            title="Open Source"
            link="Все проекты"
          />
          <div className="project-grid">
            {projects.map((project, index) => (
              <a className="project-item" href="#" key={project.name}>
                <span className="project-index">0{index + 1}</span>
                <div>
                  <h3>{project.name}</h3>
                  <p>{project.description}</p>
                </div>
                <div className="project-meta">
                  <span>★ {project.stars}</span>
                  <span>{project.tag}</span>
                </div>
              </a>
            ))}
          </div>
        </section>

        <section id="community" className="container community-section">
          <div className="community-copy">
            <span className="eyebrow">Карта сообщества</span>
            <h2>
              Python живёт
              <br />
              не только в Москве.
            </h2>
            <p>
              Локальные встречи, чаты и сообщества разработчиков по всей стране.
            </p>
            <a className="text-button" href="#">
              Найти своё сообщество <Icon name="arrow" size={17} />
            </a>
          </div>
          <div className="community-list">
            {[
              ["Moscow Python", "Москва", "12 400 участников"],
              ["SPb Python", "Санкт-Петербург", "5 800 участников"],
              ["PyLadies Russia", "Россия", "3 200 участников"],
              ["PyNSK", "Новосибирск", "1 900 участников"],
            ].map(([name, city, count]) => (
              <a href="#" key={name}>
                <strong>{name}</strong>
                <span>{city}</span>
                <small>{count}</small>
                <Icon name="arrow" size={16} />
              </a>
            ))}
          </div>
        </section>
      </main>

      <footer className="site-footer">
        <div className="container footer-top">
          <div>
            <Logo />
            <p>
              Сообщество и архив Python-разработки
              <br />
              за много лет.
            </p>
          </div>
          <div className="footer-links">
            <span>Проект</span>
            <a href="#">О Python.ru</a>
            <a href="#">Редакция</a>
            <a href="#">Архив</a>
          </div>
          <div className="footer-links">
            <span>Участвовать</span>
            <a href="#">Предложить статью</a>
            <a href="#">Добавить событие</a>
            <a href="#">Добавить проект</a>
          </div>
          <div className="footer-links">
            <span>Мы в сети</span>
            <a href="#">
              <Icon name="telegram" size={15} /> Telegram
            </a>
            <a href="#">
              <Icon name="github" size={15} /> GitHub
            </a>
            <a href="#">
              <Icon name="rss" size={15} /> RSS
            </a>
          </div>
        </div>
        <div className="container footer-bottom">
          <span>© 1999–2026 Python.ru</span>
          <span>Сделано сообществом для сообщества</span>
        </div>
      </footer>

      {searchOpen && (
        <div
          className="search-overlay"
          role="dialog"
          aria-modal="true"
          aria-label="Поиск по сайту"
          onMouseDown={() => setSearchOpen(false)}
        >
          <div
            className="search-modal"
            onMouseDown={(e) => e.stopPropagation()}
          >
            <div className="search-input-wrap">
              <Icon name="search" size={22} />
              <input
                autoFocus
                type="search"
                placeholder="Статьи, люди, проекты…"
              />
              <button
                onClick={() => setSearchOpen(false)}
                aria-label="Закрыть поиск"
              >
                <Icon name="close" />
              </button>
            </div>
            <p>
              <span>Подсказка:</span> попробуйте «asyncio», «Django» или имя
              автора
            </p>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
