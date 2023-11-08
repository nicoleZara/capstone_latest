/* JUST SOME DISCLAIMER STUFF
REMEMBER: NO JS USED */
var caring = document.querySelector('#caring'),
    click = document.querySelector('#click'),
    vis=false;
click.onclick = function() {
  if(!vis)
    caring.style.display = 'block';
  else
    caring.style.display = 'none';
  vis = !vis;
}