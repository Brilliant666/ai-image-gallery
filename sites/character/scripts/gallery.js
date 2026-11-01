(function(){
'use strict';
const $ = s => document.querySelector(s), grid = $('#grid');
const escape = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const t = (zh, ja) => PL.lang === 'ja' ? ja : zh;
const cats = DB.cats;
const items = new Map(DB.items.map(r => [r[0], {id:r[0], jp:r[1], zh:r[2], tags:r[3], cat:cats[r[4]][0], adult:!!r[5],
  set:r[0][0] === 'H' ? 'hair' : r[0][0] === 'O' ? 'outfit' : 'pose', parent:'', line:r[0][0] === 'P'}]));
const colorNames = {brown:['棕色','茶色'], black:['黑色','黒'], blonde:['金色','金'], pink:['粉色','ピンク'], silver:['银色','銀']};
for (const [id, parent] of DB.variants){
  const base = items.get(parent), color = id.split('-')[1], names = colorNames[color];
  if (base && names) items.set(id, {...base, id, parent, zh:base.zh+'（'+names[0]+'）', jp:base.jp+'('+names[1]+')'});
}
const baseItems = [...items.values()].filter(i=>!i.parent);
const cardColors = new Map();
const favKey = 'pl.character.favorites.v1';
const read = k => {try{return JSON.parse(localStorage.getItem(k));}catch(_){return null;}};
const validFav = value => new Set(Array.isArray(value) ? value.filter(id => items.has(id)) : []);
let favorites = validFav(read(favKey)), set = 'hair', category = '', query = '', color = 'brown', limit = 48, detailId = '', detailKey = '', detailLine = false, toastTimer;
const allowed = item => item && (PL.adult || !item.adult);
const label = item => PL.lang === 'ja' ? item.jp : item.zh;
const image = (item, tier='thumb') => DB.source + (tier === 'thumb' ? 'thumb/'+item.id+'.webp' : tier === 'line' ? 'line/'+item.id+'.png' : 'img/'+item.id+'.jpg');
function toast(text){
  $('#toast').textContent = text; $('#toast').hidden = false; clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {$('#toast').hidden=true;}, 3500);
}
function save(k,v){try{localStorage.setItem(k,JSON.stringify(v));}catch(_){toast(t('本浏览器未允许保存，当前收藏仍可使用。','ブラウザに保存できませんが、このページ内ではお気に入りを使えます。'));}}
async function copyTags(id, opener){
  const item=items.get(id);if(!allowed(item))return;
  try{if(!navigator.clipboard)throw Error();await navigator.clipboard.writeText(item.tags);toast(t('标签已复制','タグをコピーしました'));}
  catch(_){
    const field=document.createElement('textarea'), back=document.activeElement;
    field.value=item.tags;field.style.cssText='position:fixed;top:0;left:0;opacity:0';
    document.body.append(field);field.select();let copied=false;
    try{copied=document.execCommand('copy');}catch(_){}
    field.remove();if(back&&back.isConnected)back.focus({preventScroll:true});
    if(copied)toast(t('标签已复制','タグをコピーしました'));
    else if(allowed(item)){
      openDetail(id,opener);
      const range=document.createRange();range.selectNodeContents($('#detailTags'));
      const selection=getSelection();selection.removeAllRanges();selection.addRange(range);
      toast(t('标签已选中，请按 Ctrl/Cmd+C 复制。','タグを選択しました。Ctrl/Cmd+C でコピーしてください。'));
    }
  }
}
function colorOptions(){return Object.entries(colorNames).map(([value,names]) => '<option value="'+value+'">'+escape(t(...names))+'</option>').join('');}
const hairBase = item => item.parent || item.id;
const itemColor = item => item.parent ? item.id.split('-')[1] : 'brown';
function variant(item){
  if(item.cat!=='髪型')return item;
  const chosen=cardColors.get(item.id) || ($('#onlyFav').checked ? itemColor(item) : color), base=hairBase(item);
  return items.get(chosen==='brown'?base:base+'-'+chosen) || item;
}
function browseItems(){return $('#onlyFav').checked ? [...favorites].map(id=>items.get(id)) : baseItems;}
function currentItems(){
  const list = browseItems();
  const terms = query.normalize('NFKC').toLowerCase().split(/\s+/).filter(Boolean);
  return list.map(i=>({key:i.id,item:variant(i)})).filter(({item:i})=>allowed(i) && i.set===set && (!category || i.cat===category) && terms.every(q=>[i.id,i.parent,i.jp,i.zh,i.tags,i.cat,cats.find(c=>c[0]===i.cat)[1]].join(' ').normalize('NFKC').toLowerCase().includes(q)));
}
function drawFilters(){
  const focused=document.activeElement, group=focused.closest('#sets, #category'), value=group&&(group.id==='sets'?focused.dataset.set:focused.dataset.cat);
  const available=browseItems().filter(allowed);
  $('#sets').innerHTML = [['hair','头发与眼睛','髪・目'],['outfit','服装','衣装'],['pose','姿势','ポーズ']].map(([id,zh,ja])=>'<button type="button" data-set="'+id+'" aria-pressed="'+(set===id)+'">'+escape(t(zh,ja))+'<span>'+available.filter(i=>i.set===id).length+'</span></button>').join('');
  const options = [['',t('全部','すべて')],...cats.filter(c=>baseItems.some(i=>i.cat===c[0]&&i.set===set))];
  $('#category').innerHTML = options.map(([id,zh])=>{
    const count=available.filter(i=>i.set===set&&(!id||i.cat===id)).length;
    const gated=!PL.adult&&baseItems.some(i=>i.set===set&&i.cat===id&&i.adult)&&!baseItems.some(i=>i.set===set&&i.cat===id&&!i.adult);
    return '<button type="button" data-cat="'+escape(id)+'" aria-pressed="'+(category===id)+'">'+escape(id?(PL.lang==='ja'?id:zh):zh)+'<span>'+ (gated?'18+':count)+'</span></button>';
  }).join('');
  $('#hairColor').innerHTML = colorOptions(); $('#hairColor').value = color;
  $('#globalColors').hidden = set!=='hair' || (!!category && category!=='髪型');
  $('#hairColor').disabled = $('#globalColors').hidden;
  $('#search').placeholder=t('搜索名称、ID 或英文标签','名前・ID・英語タグを検索');
  $('#search').value=query;
  $('#sets').ariaLabel=t('分区','区分'); $('#category').ariaLabel=t('分类','分類'); $('#grid').ariaLabel=t('参考条目','参考項目');
  if(group){const key=group.id==='sets'?'set':'cat',target=[...group.querySelectorAll('button')].find(b=>b.dataset[key]===value);if(target)target.focus({preventScroll:true});}
}
function card({item,key}){
  const colors=item.cat==='髪型'?'<div class="ch-swatches" role="group" aria-label="'+escape(t('单独换色：','個別の色：')+label(items.get(hairBase(item))))+'">'+Object.entries(colorNames).map(([value,names])=>'<button type="button" class="ch-swatch ch-'+value+'" data-color="'+value+'" aria-pressed="'+(itemColor(item)===value)+'" aria-label="'+escape(t(...names))+'" title="'+escape(t(...names))+'"></button>').join('')+'</div>':'';
  return '<li class="ch-card" data-key="'+key+'" data-id="'+item.id+'">'+
    '<button class="ch-open" type="button" data-open="'+item.id+'" aria-label="'+escape(t('放大：','拡大：')+label(item))+'"><img src="'+image(item)+'" alt="'+escape(label(item))+'" loading="lazy" decoding="async"><span class="ch-img-error" hidden>'+t('图片未能加载<br>点击查看详情','画像を読み込めません<br>クリックで詳細')+'</span></button>'+
    '<div class="ch-card-body"><h3><small>'+item.id+'</small>'+escape(label(item))+'</h3><p class="ch-tags" title="'+escape(item.tags)+'">'+escape(item.tags)+'</p>'+colors+
    '<div class="ch-card-actions"><button class="btn ghost ch-copy" type="button" data-copy="'+item.id+'">'+t('复制标签','タグをコピー')+'</button><button class="btn ghost" type="button" data-fav="'+item.id+'" aria-pressed="'+favorites.has(item.id)+'" aria-label="'+escape(t('收藏：','お気に入り：')+label(item))+'">'+(favorites.has(item.id)?'★':'☆')+'</button></div></div></li>';
}
function draw(){
  const focused = grid.contains(document.activeElement) ? document.activeElement : null;
  const action = focused && ['open','copy','fav','color'].find(k=>focused.dataset[k]);
  const focusedKey = focused && focused.closest('.ch-card').dataset.key;
  const focusedColor = focused && focused.dataset.color;
  const list=currentItems();
  grid.innerHTML=list.slice(0,limit).map(card).join('');
  if(action){const card=grid.querySelector('[data-key="'+focusedKey+'"]'), target=card&&card.querySelector(action==='color'?'[data-color="'+focusedColor+'"]':'[data-'+action+']');if(target)target.focus({preventScroll:true});}
  $('#count').textContent=t(list.length+' 个条目 · 已显示 '+Math.min(limit,list.length),list.length+' 項目 · '+Math.min(limit,list.length)+' 件表示');
  $('#more').hidden=limit>=list.length; $('#empty').hidden=!!list.length;
  const hidden = [...items.values()].some(i=>!i.parent&&i.set===set&&(!category||i.cat===category)&&i.adult);
  $('#empty').innerHTML='<p>'+t('没有匹配的条目。可清除搜索、分类或收藏筛选。','一致する項目がありません。検索・分類・お気に入り条件を解除してください。')+'</p>'+(!PL.adult&&hidden?'<button type="button" class="btn ghost" data-adult-go>'+t('查看成人向参考','成人向け参考を見る')+'</button>':'');
}
function favorite(id){
  if(!items.has(id))return;
  favorites.has(id)?favorites.delete(id):favorites.add(id);save(favKey,[...favorites]);drawFilters();draw();if(detailId)syncDetailFav();
}
function syncDetailFav(){
  $('#detailFav').textContent=favorites.has(detailId)?t('★ 已收藏','★ 保存済み'):t('☆ 收藏','☆ お気に入り');
  $('#detailFav').setAttribute('aria-pressed',String(favorites.has(detailId)));
}
function renderDetail(){
  const item=items.get(detailId);if(!allowed(item))return;
  $('#detailTitle').textContent=label(item);$('#detailName').textContent=item.id+' · '+(PL.lang==='ja'?item.zh:item.jp);
  $('#detailTags').textContent=item.tags;$('#detailError').hidden=true;$('#detailImage').hidden=false;
  $('#detailImage').alt=label(item)+(detailLine?t('线稿','の線画'):'');$('#detailImage').src=image(item,detailLine?'line':'full');
  $('#original').href=image(item,'full');$('#lineLink').hidden=!item.line;
  if(item.line)$('#lineLink').href=image(item,'line');else $('#lineLink').removeAttribute('href');
  $('#line').hidden=!item.line;$('#line').setAttribute('aria-pressed',String(detailLine));
  $('#line').innerHTML=detailLine?t('查看彩图','カラーを見る'):t('查看线稿','線画を見る');
  $('#detailColors').hidden=item.cat!=='髪型';$('#detailColor').innerHTML=colorOptions();
  $('#detailColor').value=item.parent?item.id.split('-')[1]:'brown';syncDetailFav();
}
function openDetail(id,opener){
  if(!allowed(items.get(id)))return;
  detailId=id;detailKey=opener&&opener.closest('.ch-card')?opener.closest('.ch-card').dataset.key:'';detailLine=false;renderDetail();
  const key=detailKey;
  PL.openDialog($('#detail'),opener,()=>{const card=key&&grid.querySelector('[data-key="'+key+'"]');return card?card.querySelector('[data-open]'):$('#search');});
}
$('#detail').addEventListener('pl:close',()=>{detailId='';detailKey='';$('#detailImage').removeAttribute('src');$('#original').removeAttribute('href');$('#lineLink').removeAttribute('href');});
$('#detailImage').addEventListener('error',()=>{$('#detailImage').hidden=true;$('#detailError').hidden=false;});
grid.addEventListener('error',e=>{if(e.target.tagName==='IMG'){e.target.hidden=true;e.target.nextElementSibling.hidden=false;}},true);
grid.addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;if(b.dataset.open)openDetail(b.dataset.open,b);else if(b.dataset.copy)copyTags(b.dataset.copy,b);else if(b.dataset.fav)favorite(b.dataset.fav);else if(b.dataset.color){cardColors.set(b.closest('.ch-card').dataset.key,b.dataset.color);draw();}});
$('#detailCopy').addEventListener('click',e=>copyTags(detailId,e.currentTarget));$('#detailFav').addEventListener('click',()=>favorite(detailId));
$('#line').addEventListener('click',()=>{detailLine=!detailLine;renderDetail();});
$('#detailColor').addEventListener('change',()=>{const item=items.get(detailId),base=item.parent||item.id,c=$('#detailColor').value;detailId=c==='brown'?base:base+'-'+c;if(detailKey){cardColors.set(detailKey,c);draw();}renderDetail();});
function writeHash(){const h=category?'cat='+encodeURIComponent(category):'';try{history.replaceState(null,'',location.pathname+location.search+(h?'#'+h:''));}catch(_){}}
function filterChanged(){limit=48;drawFilters();draw();writeHash();}
$('#sets').addEventListener('click',e=>{const b=e.target.closest('[data-set]');if(b){set=b.dataset.set;category='';query='';filterChanged();}});
$('#category').addEventListener('click',e=>{const b=e.target.closest('[data-cat]');if(b){category=b.dataset.cat;query='';filterChanged();}});
$('#hairColor').addEventListener('change',()=>{color=$('#hairColor').value;cardColors.clear();for(const id of favorites){if(items.get(id).cat==='髪型')cardColors.set(id,color);}filterChanged();});
$('#search').addEventListener('input',()=>{query=$('#search').value;limit=48;draw();});
$('#onlyFav').addEventListener('change',()=>{limit=48;drawFilters();draw();});
$('#more').addEventListener('click',()=>{limit+=48;draw();});
$('#reset').addEventListener('click',()=>{category='';query='';color='brown';cardColors.clear();$('#onlyFav').checked=false;filterChanged();});
function readHash(){
  query='';$('#onlyFav').checked=false;
  const c=new URLSearchParams(location.hash.slice(1)).get('cat');
  if(c&&cats.some(x=>x[0]===c)){category=c;set=[...items.values()].find(i=>i.cat===c).set;}
  else category='';
  limit=48;drawFilters();draw();
}
const title = () => {document.title=t('二次元角色图库：发型、服装与姿势 · photoai.life','キャラ参考画像集：髪型・衣装・ポーズ · photoai.life');};
addEventListener('hashchange',readHash);
addEventListener('pl:lang',()=>{drawFilters();draw();if(detailId)renderDetail();title();});
addEventListener('pl:adult',()=>{if(detailId)PL.closeDialog($('#detail'));drawFilters();draw();});
addEventListener('storage',e=>{if(e.key===favKey){favorites=validFav(read(favKey));drawFilters();draw();if(detailId)syncDetailFav();}});
$('#count').title=t('原站目录版本标记：','原サイトのバージョン表記：')+DB.built;
readHash();title();
})();
