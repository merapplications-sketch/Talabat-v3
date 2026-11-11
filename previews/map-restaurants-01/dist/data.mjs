// Entire catalog is an authored design fixture, NOT a partner export.
// Coordinates are illustrative points around central Dushanbe, NOT verified premises.
// Images are the existing Talabat-v3 assets/3d illustrations, NOT restaurant photos.
const text=(ru,en)=>({ru,en});
const definitions=[
  ['demo-safran-center','safran','Сафран','Safran','Центр','Centre','restaurant',38.5763,68.7863,true,'bread',[5,4,5]],
  ['demo-safran-north','safran','Сафран','Safran','Север','North','restaurant',38.5922,68.7862,false,'bread',[4,4]],
  ['demo-pizza','pizza','Пицца & Ко','Pizza & Co','Рудаки','Rudaki','fastfood',38.5688,68.7941,true,'pizza',[5,5,4,5]],
  ['demo-coffee','coffee','Утро','Morning','Парк','Park','cafe',38.5798,68.7745,true,'croissant',[5,4]],
  ['demo-burger','burger','Бургерная','Burger House','Юг','South','fastfood',38.5595,68.7882,true,'hamburger',[]],
  ['demo-sushi','sushi','Сакура','Sakura','Восток','East','restaurant',38.5826,68.7983,false,'sushi',[3,4,5]],
];
const comments=[text('Вкусно, блюдо приехало аккуратно упакованным.','Tasty food, carefully packed.'),text('Хороший вкус. Хотелось бы чуть больше соуса.','Good flavour. A little more sauce would be nice.'),text('Заказывали на ужин, всё понравилось.','Ordered dinner and enjoyed everything.'),text('Будем заказывать ещё.','We would order again.')];
export const stores=definitions.map(([id,brand_id,ru,en,brRu,brEn,category,lat,lng,is_open,asset,scores])=>({
  id,brand_id,name:text(ru,en),branch:text(brRu,brEn),category,lat,lng,is_open,is_active:true,
  address:text('Душанбе · '+brRu+' · пример расположения','Dushanbe · '+brEn+' · illustrative location'),
  image:'assets/'+asset+'.webp',image_kind:'illustration',
  talabot_rating:{source:'talabot',subject:'restaurant',store_id:id,rating_average:scores.length?Math.round(scores.reduce((a,b)=>a+b,0)/scores.length*10)/10:null,rating_count:scores.length},
  reviews:scores.map((stars,i)=>({id:id+'-review-'+i,store_id:id,source:'talabot',subject:'restaurant',stars,author:text('Демо-гость '+(i+1),'Demo guest '+(i+1)),date:'2026-11-'+String(10-i).padStart(2,'0'),comment:comments[i%comments.length]})),
  menu:[{id:id+'-dish-1',name:text(category==='cafe'?'Круассан':'Фирменное блюдо',category==='cafe'?'Croissant':'Signature dish'),description:text('Пример блюда для проверки перехода в меню','Sample dish for the menu navigation preview'),price:category==='cafe'?18:45,image:'assets/'+asset+'.webp'},
    {id:id+'-dish-2',name:text('Свежий хлеб','Fresh bread'),description:text('Демонстрационная позиция','Demonstration menu item'),price:8,image:'assets/bread.webp'}]
}));
export const provenance={mode:'synthetic',catalog:'Authored MAP-RESTAURANTS-01 fixture, 2026-11-12',coordinates:'Illustrative Dushanbe coordinates; not actual partner locations',ratings:'Authored restaurant-only TALABOT-schema examples; no live or Google reviews',images:'Existing Talabat-v3 assets/3d/*.webp illustrations',policy:'05428e37d9779fa2af0845e640fe85553c8b6974'};
