const { extract, getSanitizeHtmlOptions, setSanitizeHtmlOptions, addTransformations } = require('@extractus/article-extractor');

const input = process.argv[2]
// Index 0 and index 1 are reserved for the Node.js executable and script path, respectively.
const rightTag = /<\/(?:"[^"]*"['"]*|'[^']*'['"]*|[^'">])+>/g;
const leftTag = /<(?:"[^"]*"['"]*|'[^']*'['"]*|[^'">])+>/g;


(async () => {
  try {
    addTransformations({
      patterns: [
        /([\w]+.)?politico.com\/*/
      ],
      pre: (document) => {
        // remove all .advertise-area and its siblings from raw HTML content
        const headers = document.querySelectorAll('header.block-p-header');
        if (headers.length > 0) {
          const firstHeader = headers[0];
          let currentNode = firstHeader;
          while (currentNode.nextSibling) {
            currentNode.parentNode.removeChild(currentNode.nextSibling);
          }
        }
        return document
      },
      post: (document) => {
        return document
      }
    })
    const article = await extract(input)
    //console.log(article)
    if(article != null){
      //console.log(`article title is ${article.title}`);
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