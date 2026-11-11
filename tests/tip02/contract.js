/* TIP-02 new non-null numeric contract. Explicit NULL policy remains separate. */
function tipNumber02(value){return {ok:typeof value==='number'&&Number.isFinite(value)&&Number.isInteger(value)&&value>=0&&value<=100,value};}
