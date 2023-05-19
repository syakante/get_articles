const { extract, getSanitizeHtmlOptions, setSanitizeHtmlOptions } = require('@extractus/article-extractor');
//const sanitizeHtml = require('sanitize-html');

//needs js input:
//const input = 'https://www.taipeitimes.com/News/editorials/archives/2023/05/19/2003800050';
//regular input:
//const input = 'https://www.nbcnews.com/news/world/china-unlikely-play-peacemaker-role-ukraine-war-rcna84074';
//kcna input (bricked):
const input = 'https://kcnawatch.org/newstream/1452058173-983528564/%eb%a1%9c%eb%8f%99%ec%8b%a0%eb%ac%b8-%ec%a1%b0%ec%84%a0%eb%b0%98%eb%8f%84-%eb%b9%84%ed%95%b5%ed%99%94%eb%8a%94-%ec%a1%b0%ec%84%a0%ec%9d%98-%ea%b5%b0%eb%8c%80%ec%99%80-%ec%9d%b8%eb%af%bc%ec%9d%98/';
//some kr input
//const input = 'https://www.newdaily.co.kr/site/data/html/2023/05/08/2023050800194.html';
const mySanitizeOptions = {
  allowedTags: ['p'],
  allowedAttributes: {}
}
const rightTag = /<\/(?:"[^"]*"['"]*|'[^']*'['"]*|[^'">])+>/g;
const leftTag = /<(?:"[^"]*"['"]*|'[^']*'['"]*|[^'">])+>/g;
setSanitizeHtmlOptions(mySanitizeOptions);

// here we use top-level await, assume current platform supports it
(async () => {
  try {
    const article = await extract(input)
    //console.log(article)
    if(article != null){
      console.log(`article title is ${article.title}`);
      //rawContent = sanitizeHtml(article.content, { allowedTags: myAllowedTags });
      //console.log(getSanitizeHtmlOptions())
      articleText = article.content.replace(rightTag, '').replace(leftTag, ' ');
      console.log(articleText);
      return
    } else {
      console.log("Got null. Seems like the webpage needs be rendered with JS client-side.");
    }
  } catch (err) {
    console.error(err);
  }
})();