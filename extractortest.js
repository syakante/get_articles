const { extract, getSanitizeHtmlOptions, setSanitizeHtmlOptions } = require('@extractus/article-extractor');

//example of js input:
//const input = 'https://www.taipeitimes.com/News/editorials/archives/2023/05/19/2003800050';

//const input = 'https://koreajoongangdaily.joins.com/2022/11/21/opinion/columns/Korea-Australia-middle-power/20221121193437683.html';
const input = process.argv[2]
const mySanitizeOptions = {
  allowedTags: ['p']
  //allowedAttributes: {'header': ['class']}
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
      //console.log(`article title is ${article.title}`);
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