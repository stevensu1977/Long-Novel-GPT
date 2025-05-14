package main

import (
	"fmt"
	"log"
	"net/http"
	"net/http/httputil"
	"net/url"
	"strings"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
)

func main() {
	r := gin.Default()

	// 配置CORS
	config := cors.DefaultConfig()
	config.AllowAllOrigins = true
	config.AllowMethods = []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"}
	config.AllowHeaders = []string{"Origin", "Content-Type", "Accept", "Authorization", "X-Requested-With"}
	r.Use(cors.New(config))

	// 创建反向代理
	target, err := url.Parse("http://127.0.0.1:7869")
	if err != nil {
		log.Fatal(err)
	}

	proxy := httputil.NewSingleHostReverseProxy(target)

	// 修改代理的Director函数
	originalDirector := proxy.Director
	proxy.Director = func(req *http.Request) {
		originalDirector(req)
		// 移除 /api 前缀
		fmt.Println("req.URL.Path: ", req.URL.Path)
		req.URL.Path = strings.TrimPrefix(req.URL.Path, "/api")
		// 设置其他必要的头部
		req.Header.Set("X-Forwarded-Proto", "http")
	}

	// 修改代理的ModifyResponse函数
	proxy.ModifyResponse = func(resp *http.Response) error {
		// 添加CORS头部
		resp.Header.Set("Access-Control-Allow-Origin", "*")
		resp.Header.Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
		resp.Header.Set("Access-Control-Allow-Headers", "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range")
		return nil
	}

	// 处理OPTIONS请求
	r.OPTIONS("/api/*path", func(c *gin.Context) {
		c.Header("Access-Control-Allow-Origin", "*")
		c.Header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
		c.Header("Access-Control-Allow-Headers", "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range")
		c.Status(http.StatusOK)
	})

	// 处理所有其他API请求
	r.POST("/api/*path", func(c *gin.Context) {
		proxy.ServeHTTP(c.Writer, c.Request)
	})
	r.GET("/api/*path", func(c *gin.Context) {
		proxy.ServeHTTP(c.Writer, c.Request)
	})
	r.PUT("/api/*path", func(c *gin.Context) {
		proxy.ServeHTTP(c.Writer, c.Request)
	})
	r.DELETE("/api/*path", func(c *gin.Context) {
		proxy.ServeHTTP(c.Writer, c.Request)
	})

	// 静态文件服务 - 使用 NoRoute 处理所有未匹配的路由
	r.NoRoute(func(c *gin.Context) {
		// 检查是否是API请求
		if strings.HasPrefix(c.Request.URL.Path, "/api") {
			c.Status(http.StatusNotFound)
			return
		}
		if c.Request.URL.Path == "/" {
			c.File("./frontend/index.html")
			return
		}
		// 否则尝试提供静态文件
		fileServer := http.FileServer(http.Dir("./frontend"))
		fileServer.ServeHTTP(c.Writer, c.Request)
	})

	// 启动服务器
	log.Println("Server starting on http://localhost:8080")
	if err := r.Run(":8080"); err != nil {
		log.Fatal(err)
	}
}
