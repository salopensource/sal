"use strict";

// Plugins
var            gulp = require( 'gulp' ),
            connect = require( 'connect' ),
  connectLivereload = require( 'connect-livereload' ),
     gulpLivereload = require( 'gulp-livereload' ),
               less = require('gulp-less'),
             prefix = require( 'gulp-autoprefixer' ),
             jshint = require( "gulp-jshint" ),
            stylish = require( 'jshint-stylish' );

// paths & files
var path = {
        src: 'site_static/',
       html: 'site_static/**/*.html',
         js: 'site_static/js/*.js',
       less: 'site_static/less/**/*.less',
        css: 'site_static/css/',
};

// ports
var localPort =  8000,
       lrPort = 35729;

// start local server
gulp.task( 'server', function() {
  var server = connect();

  server.use( connectLivereload( { port: lrPort } ) );
  server.use( connect.static( path.src ) );
  server.listen( localPort );

  console.log( "\nlocal server running at http://localhost:" + localPort + "/\n" );
});

// jshint
gulp.task( 'jshint', function() {
  gulp.src( path.js )
    .pipe( jshint() )
    .pipe( jshint.reporter( stylish ) );
});

// compile less
gulp.task('less', function(){
  gulp.src('site_static/less/**/*.less')
  .pipe(less())
  .pipe(gulp.dest('site_static/css/'));
});

// watch file
gulp.task( 'watch', function(done) {
  var lrServer = gulpLivereload();

  gulp.watch( [ path.html, path.js, path.css + '/**/*.css' ] )
    .on( 'change', function( file ) {
      lrServer.changed( file.path );
    });

  gulp.watch( path.js, ['jshint'] );

  gulp.watch( path.less, ['less'] );
});

// default task
gulp.task( 'default', [ 'watch', 'less' ] );
