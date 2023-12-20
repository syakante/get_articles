const { extract } = require('@extractus/article-extractor');

//example of js input:
//const input = 'https://www.taipeitimes.com/News/editorials/archives/2023/05/19/2003800050';

//const input = 'https://koreajoongangdaily.joins.com/2022/11/21/opinion/columns/Korea-Australia-middle-power/20221121193437683.html';
const input = process.argv[2];
// here we use top-level await, assume current platform supports it

(async () => {
  try {
    const article = await extract(input)
    //console.log(article)
    if(article != null){
      var myAuthor = article.author.length === 0 ? "authorNotFound_node":article.author.trim();
      var myTitle = article.title.length === 0 ? "titleNotFound_node":article.title.trim();
      console.log(`${myTitle}\t${myAuthor}`); //string output
      return
    } else {
      console.log("authorParseError_Node_gotNull");
    }
  } catch (err) {
    if(err.response){
      console.log(err.response.status)
    } else {
      console.log("authorParseError_Node")
    }
  }
})();