import React from 'react';
import {Composition,registerRoot} from 'remotion';
import {ChapterCard} from './Card';
registerRoot(()=> <Composition id="ChapterCard" component={ChapterCard} width={1920} height={1080} fps={30} durationInFrames={1} defaultProps={{title:'関ヶ原を、地形から読む',category:'史料参照＋現代実測地形',source:'GSI_DEM / MUSEUM'}}/>);
