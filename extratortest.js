const { extract } = require('@extractus/article-extractor');

const input = 'https://www.nbcnews.com/news/world/china-unlikely-play-peacemaker-role-ukraine-war-rcna84074';

// here we use top-level await, assume current platform supports it
(async () => {
  try {
    const article = await extract(input)
    console.log(article)
  } catch (err) {
    console.error(err)
  }
})();